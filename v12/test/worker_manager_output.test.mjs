// W2929 item 3, fourth slice: the output freeze.
//
// Every case asks the same question the rest of this manager asks: what is
// durably true afterwards, and what did the manager REFUSE to write down
// because nothing it could read said so.
//
// The adapter's sealed observation is a real `baton.worker-manifest/result`
// document, validated by the shared manifest entry rather than by a shape
// this suite invented. That matters: a fixture that only satisfies the
// implementation proves the two agree with each other.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { V12Authority, V12 } from "../src/authority/index.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { activateAssignment, observe, recordAttempt }
	from "../src/worker_manager/attempts.mjs";
import { loadManifest, retainManifest }
	from "../src/worker_manager/manifests.mjs";
import { freezeOperation, freezeOperationId, recordFrozenResult,
         recordOperationId, requestFreeze }
	from "../src/worker_manager/output.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const WHO = "poc.claude";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const ASSIGNMENT = { authorityUuid: UUID, workId: WORK, participant: WHO,
                     generation: 1 };
const POLICY = digest("policy");

function storePath() {
	return join(ownedTemp("v12-manager-"), "control.sqlite3");
}

function open(path = storePath()) {
	return new ControlStore(path, { incarnation: "manager-1",
		clock: () => NOW });
}

function session({ assignment = ASSIGNMENT, participant = WHO } = {}) {
	return { participant, assignmentOf: () => assignment };
}

function adapter({ seal = null } = {}) {
	const calls = [];
	return {
		calls,
		seal(operands) {
			calls.push(["seal", operands]);
			return seal === null ? result() : seal(operands);
		},
	};
}

/** The claimed offer activation requires, written straight in — the offer
 *  path has its own suite. */
function claimed(store, assignment = ASSIGNMENT, inputDigest = INPUT) {
	store.db.prepare(
		"INSERT INTO offers (offer_id, work_id, authority_uuid, participant, "
		+ "runtime_attempt_id, incarnation, input_digest, policy_digest, "
		+ "profile_digest, verifier, verifier_spent, issued_at, expires_at, "
		+ "state, claim_generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, "
		+ "?, ?, 'claimed', ?)")
		.run(`offer-for-${assignment.workId}-${assignment.generation}`,
		     assignment.workId, assignment.authorityUuid,
		     assignment.participant, ATTEMPT, "manager-1", inputDigest, POLICY,
		     digest("profile"), `sha256:${"0".repeat(64)}`, NOW,
		     "2026-08-22T13:00:00.000Z", assignment.generation);
}

// The declared route to each execution state, spelled out rather than
// walked: a fixture that drives "until it matches" silently reaches a
// different state when the map changes, and then asserts about that one.
const EXECUTION_PATHS = Object.freeze({
	"not-started": [],
	uncertain: ["uncertain"],
	running: ["start-requested", "running"],
	stopping: ["start-requested", "running", "stopping"],
	quiescent: ["start-requested", "running", "quiescent"],
});

/** An attempt whose writer has stopped and whose outcome is recorded: the
 *  state a freeze actually finds. */
function quiesced(store, { api = session(), assignment = ASSIGNMENT,
                           disposition = "completed", execution = "quiescent",
                           declared = DECLARATION } = {}) {
	// The attempt names the declaration it was actually given, so a case
	// that varies the declaration varies what the freeze compares against.
	const inputDigest = (declared ?? DECLARATION).manifest_digest;
	if (declared !== null) retainManifest(store, declared, "inputManifest");
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile"),
		inputDigest, policyDigest: POLICY });
	claimed(store, assignment, inputDigest);
	activateAssignment(store, api, { attemptId: ATTEMPT, expect: assignment });
	for (const value of EXECUTION_PATHS[execution]) {
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value });
	}
	if (disposition !== "none") {
		observe(store, { attemptId: ATTEMPT, axis: "worker_disposition",
			value: disposition });
	}
	return ATTEMPT;
}

function row(store) {
	return store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id=?").get(ATTEMPT);
}

function outputRow(store) {
	return store.db.prepare(
		"SELECT * FROM outputs WHERE runtime_attempt_id=?").get(ATTEMPT);
}

function entries(paths) {
	return paths.map((path) => ({ path, bytes: path.length,
	                              content_digest: digest(path) }));
}

function manifest(entryList) {
	return { entries: entryList, entry_count: entryList.length,
	         total_bytes: entryList.reduce((sum, e) => sum + e.bytes, 0),
	         tree_digest: digest(entryList) };
}

function artifact(id = "artifact-1") {
	return { artifact_id: id, media_type: "application/zip", bytes: 12,
	         content_digest: digest(id),
	         locator: `artifact://store/${id}` };
}

function freezeSignature({ assignment = ASSIGNMENT, disposition = "completed",
	freezeId = FREEZE_ID } = {}) {
	return digest({ kind: "output.freeze", operands: {
		attemptId: ATTEMPT, expect: assignment, disposition,
		operationId: freezeId } });
}

const CONSTRAINTS = { max_bytes: 1048576, max_entries: 1000,
                      allowed_media_types: ["application/zip"],
                      link_policy: "forbid", validator_digest: null };

/** A real INPUT manifest — the declaration a sealed result is compared
 *  against. Its digest is what the attempt records, so a fixture that skipped
 *  retaining it would be a fixture whose freeze cannot check anything. */
function declaration({ outputs = null } = {}) {
	const body = {
		version: { major: 1, minor: 0 },
		manifest_id: "input-1",
		created_at: NOW,
		extensions: {},
		schema: "baton.worker-manifest/input",
		work_ref: { authority_uuid: UUID, work_id: WORK },
		assignment_contract: "v12-assignment-1",
		human_contract: artifact("contract-1"),
		sources: [{ name: "source", type: "directory",
		            uri: "artifact://store/source-1", destination: "in",
		            required: true,
		            content_manifest: manifest(entries(["seed.txt"])) }],
		outputs: outputs ?? [{ name: "result-tree", type: "directory-result",
		                       path: "out", required: true,
		                       constraints: CONSTRAINTS }],
		role_instructions_digest: digest("role"),
		policy_digest: POLICY,
		toolchain_digest: digest("toolchain"),
		worker_image_digest: digest("image"),
		runtime_profile_digest: digest("profile"),
		resource_policy_digest: digest("resource"),
		network_policy_digest: digest("network"),
		mount_policy_digest: digest("mount"),
		tool_policy_digest: digest("tool"),
		credential_policy_digest: digest("credential"),
		retention_policy_digest: digest("retention"),
		record_binding: { root: "work", path: "records/f/PLAN.md",
		                  finding_digest: digest("finding"),
		                  plan_digest: digest("plan") },
	};
	return { ...body, manifest_digest: digest(body) };
}

// THE ATTEMPT'S INPUT DIGEST IS THE DECLARATION'S. It was an unrelated
// `digest("input")` before, which is precisely why nothing could be compared
// against the declaration: the number named no document.
const DECLARATION = declaration();
const INPUT = DECLARATION.manifest_digest;

/** A real result manifest, sealed the way the contract says. The digest is
 *  computed LAST, over the document with `manifest_digest` omitted. */
function result({ assignment = ASSIGNMENT, disposition = "completed",
                  freezeId = null, inputDigest = INPUT,
                  policyDigest = POLICY, resultId = "result-1",
	              freezeSignatureDigest = null, outputs = null } = {}) {
	const effectiveFreezeId = freezeId ?? FREEZE_ID;
	const body = {
		version: { major: 1, minor: 0 },
		manifest_id: "manifest-1",
		created_at: NOW,
		extensions: {},
		schema: "baton.worker-manifest/result",
		result_id: resultId,
		assignment_ref: {
			work_ref: { authority_uuid: assignment.authorityUuid,
			            work_id: assignment.workId },
			participant: assignment.participant,
			generation: assignment.generation,
		},
		input_manifest_digest: inputDigest,
		policy_digest: policyDigest,
		disposition,
		outputs: outputs ?? [{
			name: "result-tree", type: "directory-result", status: "present",
			content_manifest: manifest(entries(["a.txt", "b.txt"])),
			artifact: artifact(),
		}],
		evidence: [],
		freeze_operation: {
			operation_id: effectiveFreezeId,
			signature_digest: freezeSignatureDigest
				?? freezeSignature({ assignment, disposition,
				                     freezeId: effectiveFreezeId }),
		},
		manager_observed_at: NOW,
	};
	return { ...body, manifest_digest: digest(body) };
}

// The freeze identity is derived from the attempt and its assignment, both
// of which are fixed by the fixture, so it can be named before the act.
const FREEZE_ID = `output.freeze:${digest({
	attemptId: ATTEMPT, assignment: ASSIGNMENT }).slice("sha256:".length)}`;

// -- the happy path, and what it wrote --------------------------------------

test("W2929: a freeze records the sealed result immutably", () => {
	const store = open();
	try {
		quiesced(store);
		assert.equal(freezeOperationId(row(store)), FREEZE_ID,
			"the derived freeze identity is not what the fixture names");
		const runtime = adapter();
		const answer = requestFreeze(store, session(), runtime,
			{ attemptId: ATTEMPT, disposition: "completed" });
		assert.equal(answer.resultId, "result-1");
		assert.equal(row(store).output, "frozen");
		const stored = outputRow(store);
		assert.equal(stored.result_id, "result-1");
		assert.equal(stored.disposition, "completed");
		assert.equal(stored.freeze_operation_id, FREEZE_ID);
		assert.equal(stored.manifest_digest, answer.manifestDigest);
		// The artifact REFERENCE is durable; whether its bytes match is
		// W2930's collection-time fact.
		const refs = store.db.prepare(
			"SELECT * FROM output_artifacts WHERE runtime_attempt_id=?")
			.all(ATTEMPT);
		assert.equal(refs.length, 1);
		assert.equal(refs[0].output_name, "result-tree");
		assert.equal(refs[0].locator, "artifact://store/artifact-1");
	} finally {
		store.close();
	}
});

test("W2929: the adapter is told which act it is sealing", () => {
	const store = open();
	try {
		quiesced(store);
		const runtime = adapter();
		requestFreeze(store, session(), runtime,
			{ attemptId: ATTEMPT, disposition: "completed" });
		const [, operands] = runtime.calls.find(([what]) => what === "seal");
		// THE WHOLE identity, not just the retry key: an adapter handed only
		// the id cannot echo the binding the record then demands.
		assert.deepEqual(operands.operation, {
			operation_id: FREEZE_ID, signature_digest: freezeSignature() });
		assert.deepEqual(operands.assignment, ASSIGNMENT);
		assert.equal(operands.disposition, "completed");
	} finally {
		store.close();
	}
});

// -- the same digest replays; changed bytes refuse --------------------------

test("W2929: the same sealed result replays and writes nothing twice", () => {
	const store = open();
	try {
		quiesced(store);
		const first = requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" });
		// The freeze act is over; the record is replayed directly, which is
		// what a restart mid-freeze does.
		const again = recordFrozenResultAfterFreeze(store);
		assert.deepEqual(again, first, "the replay was re-derived, not replayed");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM outputs").get().n, 1);
	} finally {
		store.close();
	}
});

test("W2929 review: an exact result replays after the output axis advances",
	() => {
		const store = open();
		try {
			quiesced(store);
			const sealed = result();
			const first = requestFreeze(store, session(),
				adapter({ seal: () => sealed }),
				{ attemptId: ATTEMPT, disposition: "completed" });
			observe(store, { attemptId: ATTEMPT, axis: "output", value: "sealed" });
			assert.deepEqual(recordFrozenResult(store,
				{ attemptId: ATTEMPT, sealed }), first,
				"later output state hid the committed result operation replay");
			assert.equal(row(store).output, "sealed");
		} finally {
			store.close();
		}
	});

test("W2929 review: an exact result replay does not require its old input row",
	() => {
		const store = open();
		try {
			quiesced(store);
			const sealed = result();
			const first = requestFreeze(store, session(),
				adapter({ seal: () => sealed }),
				{ attemptId: ATTEMPT, disposition: "completed" });
			// The result operation is already committed. Later retention cleanup
			// may remove an input document, but it cannot make the journal forget
			// what this fixed result identity settled.
			store.db.prepare("DELETE FROM manifests WHERE digest = ?").run(INPUT);
			assert.deepEqual(recordFrozenResult(store,
				{ attemptId: ATTEMPT, sealed }), first,
				"current retention state hid a committed result replay");
		} finally {
			store.close();
		}
	});

/** Recording again against an already-frozen attempt goes through the
 *  journal, which is where replay is decided. The axis precondition would
 *  refuse first, so this drives the identity the way a crashed manager
 *  would: re-request the freeze it already committed. */
function recordFrozenResultAfterFreeze(store) {
	return requestFreeze(store, session(), adapter(),
		{ attemptId: ATTEMPT, disposition: "completed" });
}

test("W2929: CHANGED BYTES under the same freeze refuse", () => {
	const store = open();
	try {
		quiesced(store);
		requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" });
		// A different result under the SAME act. The identity is the act, so
		// this is a collision rather than a second record — if the identity
		// varied with the bytes, both would simply commit.
		const other = adapter({ seal: () => result({ resultId: "result-2" }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.code === "operation-collision");
		assert.equal(outputRow(store).result_id, "result-1");
	} finally {
		store.close();
	}
});

test("W2929: the record identity is the ACT, not the bytes", () => {
	const store = open();
	try {
		quiesced(store);
		const before = recordOperationId(row(store));
		requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" });
		assert.equal(recordOperationId(row(store)), before,
			"the record identity moved with the result it recorded");
	} finally {
		store.close();
	}
});

// -- the preconditions ------------------------------------------------------

test("W2929: an unquiesced writer cannot be frozen", () => {
	for (const execution of ["running", "stopping", "uncertain",
	                         "not-started"]) {
		const store = open();
		try {
			quiesced(store, { execution });
			const runtime = adapter();
			assert.throws(() => requestFreeze(store, session(), runtime,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "quiescence-unknown", execution);
			assert.equal(runtime.calls.length, 0, execution);
			assert.equal(row(store).output, "open", execution);
		} finally {
			store.close();
		}
	}
});

test("W2929: a DESTROYED writer is not a quiesced one", () => {
	const store = open();
	try {
		quiesced(store, { execution: "running" });
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "destroyed" });
		// Gone is not finished. A writer nobody watched stop never produced
		// an observation that its tree had stopped changing.
		assert.throws(() => requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.code === "quiescence-unknown");
	} finally {
		store.close();
	}
});

test("W2929: a freeze needs a RECORDED terminal disposition", () => {
	const store = open();
	try {
		quiesced(store, { disposition: "none" });
		const runtime = adapter();
		assert.throws(() => requestFreeze(store, session(), runtime,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& /no recorded worker disposition/.test(error.message));
		assert.equal(runtime.calls.length, 0);
	} finally {
		store.close();
	}
});

test("W2929: the declared disposition is COMPARED against the recorded one",
	() => {
		const store = open();
		try {
			quiesced(store, { disposition: "unable" });
			const runtime = adapter();
			assert.throws(() => requestFreeze(store, session(), runtime,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "refused"
					&& /recorded disposition unable/.test(error.message));
			assert.equal(runtime.calls.length, 0);
		} finally {
			store.close();
		}
	});

test("W2929: a dead or moved assignment publishes nothing", () => {
	for (const [what, live] of [
			["ended", null],
			["a newer generation", { ...ASSIGNMENT, generation: 2 }],
			["another participant", { ...ASSIGNMENT, participant: "poc.other" }],
			["another authority",
			 { ...ASSIGNMENT, authorityUuid: "f".repeat(32) }]]) {
		const store = open();
		try {
			quiesced(store);
			const runtime = adapter();
			assert.throws(() => requestFreeze(store,
				session({ assignment: live }), runtime,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "stale-assignment", what);
			assert.equal(runtime.calls.length, 0, what);
			assert.equal(row(store).output, "open", what);
		} finally {
			store.close();
		}
	}
});

test("W2929: a foreign session cannot freeze this attempt", () => {
	const store = open();
	try {
		quiesced(store);
		const runtime = adapter();
		assert.throws(() => requestFreeze(store,
			session({ participant: "poc.other" }), runtime,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "capability");
		assert.equal(runtime.calls.length, 0);
	} finally {
		store.close();
	}
});

test("W2929: an unactivated attempt has no generation to publish under", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.throws(() => requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

test("W2929: an adapter without seal() is refused before anything moves", () => {
	const store = open();
	try {
		quiesced(store);
		assert.throws(() => requestFreeze(store, session(), {},
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
		assert.equal(row(store).output, "open");
	} finally {
		store.close();
	}
});

// -- validating the adapter's sealed observation ----------------------------

test("W2929: a sealed result for another assignment is refused", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			assignment: { ...ASSIGNMENT, generation: 7 } }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment"
				&& error.code === "target");
		assert.equal(outputRow(store), undefined);
	} finally {
		store.close();
	}
});

test("W2929: a sealed result naming another input or policy is refused", () => {
	for (const [what, overrides] of [
			["input", { inputDigest: digest("elsewhere") }],
			["policy", { policyDigest: digest("elsewhere") }]]) {
		const store = open();
		try {
			quiesced(store);
			const other = adapter({ seal: () => result(overrides) });
			assert.throws(() => requestFreeze(store, session(), other,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest", what);
		} finally {
			store.close();
		}
	}
});

test("W2929: a sealed result settling another freeze is refused", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			freezeId: "output.freeze:somebody-else" }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /this attempt's freeze is/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929 review: a sealed result must echo the freeze signature", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			freezeSignatureDigest: digest("another freeze signature") }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
		assert.equal(outputRow(store), undefined);
	} finally {
		store.close();
	}
});

test("W2929: a sealed result declaring another disposition is refused", () => {
	const store = open();
	try {
		quiesced(store);
		// The freeze REQUEST and the recorded axis agree; the document does
		// not. Three places must say the same thing, and two agreeing is how
		// the third gets in.
		const other = adapter({ seal: () => result({ disposition: "unable" }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /sealed result declares unable/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a tampered sealed result is refused by its own digest", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => {
			const sealed = result();
			// One byte of the tree, with the manifest digest left alone —
			// the shape a store or a transport can produce and a reader
			// cannot see without recomputing.
			sealed.outputs[0].content_manifest.entries[0].bytes += 1;
			return sealed;
		} });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
		assert.equal(outputRow(store), undefined);
	} finally {
		store.close();
	}
});

test("W2929: an unsorted content manifest is refused", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({ outputs: [{
			name: "result-tree", type: "directory-result", status: "present",
			content_manifest: manifest(entries(["b.txt", "a.txt"])),
			artifact: artifact(),
		}] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /sorted bytewise and unique/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a locator carrying a credential never lands", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({ outputs: [{
			name: "result-tree", type: "directory-result", status: "present",
			content_manifest: manifest(entries(["a.txt"])),
			artifact: { ...artifact(),
			            locator: "https://user:secret@store/artifact-1" },
		}] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM output_artifacts").get().n, 0,
			"a credential-bearing locator reached a durable row");
	} finally {
		store.close();
	}
});

test("W2929: nothing is recorded when validation refuses", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => ({ not: "a manifest" }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError);
		// The freeze REQUEST stands — it happened, and a restart must be able
		// to see that it did — but no result was recorded.
		assert.equal(row(store).output, "freeze-requested");
		assert.equal(outputRow(store), undefined);
	} finally {
		store.close();
	}
});

test("W2929: a result cannot be recorded against an unrequested freeze", () => {
	const store = open();
	try {
		quiesced(store);
		assert.throws(() => recordFrozenResult(store,
			{ attemptId: ATTEMPT, sealed: result() }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

// -- against a real authority -----------------------------------------------

test("W2929: the whole freeze, against a real authority", () => {
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	const store = open(join(root, "control.sqlite3"));
	try {
		authority.certifyContract(V12);
		authority.addRouteHandler("impl", WHO);
		authority.createWork({ workId: WORK, route: "impl", contract: V12 });
		const api = authority.session(WHO);
		const assignment = api.claim({ workId: WORK, operationId: "claim-1" });
		quiesced(store, { api, assignment });
		const freezeId = freezeOperationId(row(store));
		const runtime = adapter({ seal: () => result({ assignment, freezeId }) });
		const answer = requestFreeze(store, api, runtime,
			{ attemptId: ATTEMPT, disposition: "completed" });
		assert.equal(answer.resultId, "result-1");
		assert.equal(row(store).output, "frozen");
		// AND THE AUTHORITY IS UNTOUCHED. A freeze is a manager-side record;
		// it publishes nothing and ends nothing.
		const work = api.projectWork(WORK);
		assert.equal(work.handler, WHO);
		assert.equal(work.phase, "active");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: freezing after the real assignment ended is refused", () => {
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	const store = open(join(root, "control.sqlite3"));
	try {
		authority.certifyContract(V12);
		authority.addRouteHandler("impl", WHO);
		authority.createWork({ workId: WORK, route: "impl", contract: V12 });
		const api = authority.session(WHO);
		const assignment = api.claim({ workId: WORK, operationId: "claim-1" });
		quiesced(store, { api, assignment });
		api.cancel({ expect: assignment, operationId: "cancel-1",
			reason: "operator" });
		const runtime = adapter();
		assert.throws(() => requestFreeze(store, api, runtime,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment");
		assert.equal(runtime.calls.length, 0);
		assert.equal(row(store).output, "open");
	} finally {
		store.close();
		authority.dispose();
	}
});

// -- the sealed result against the DECLARATION ------------------------------

const OPTIONAL_DECL = declaration({ outputs: [
	{ name: "result-tree", type: "directory-result", path: "out",
	  required: true, constraints: CONSTRAINTS },
	{ name: "notes", type: "record-output", path: "notes",
	  required: false, constraints: CONSTRAINTS },
] });

function answered(name, { type = "directory-result", status = "present" } = {}) {
	if (status !== "present") {
		return { name, type, status, content_manifest: null, artifact: null };
	}
	return { name, type, status,
	         content_manifest: manifest(entries(["a.txt"])),
	         artifact: artifact(`artifact-${name}`) };
}

test("W2929: an UNDECLARED output is never recorded", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			outputs: [answered("somewhere-else")] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /does not declare/.test(error.message));
		assert.equal(outputRow(store), undefined);
	} finally {
		store.close();
	}
});

test("W2929: a DECLARATION the result never answers is refused", () => {
	const store = open();
	try {
		quiesced(store, { declared: OPTIONAL_DECL });
		// Only the required one is answered. A declaration dropped from the
		// result is not an answer to it.
		const other = adapter({ seal: () => result({
			inputDigest: OPTIONAL_DECL.manifest_digest,
			outputs: [answered("result-tree")] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /does not answer it/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a MISSING REQUIRED output is not a completion", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({ outputs: [
			answered("result-tree", { status: "missing-optional" })] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /under a completed disposition/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: an INABILITY may report a missing required output", () => {
	const store = open();
	try {
		quiesced(store, { disposition: "unable" });
		// The pinned sentence's other half: an inability disposition may
		// return evidence without pretending the requested result exists.
		const other = adapter({ seal: () => result({ disposition: "unable",
			outputs: [answered("result-tree", { status: "missing-optional" })] }) });
		const answer = requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "unable" });
		assert.equal(answer.disposition, "unable");
		assert.equal(row(store).output, "frozen");
	} finally {
		store.close();
	}
});

test("W2929: an OPTIONAL output may be absent from a completion", () => {
	const store = open();
	try {
		quiesced(store, { declared: OPTIONAL_DECL });
		const other = adapter({ seal: () => result({
			inputDigest: OPTIONAL_DECL.manifest_digest,
			outputs: [answered("result-tree"),
			          answered("notes", { type: "record-output",
			                              status: "missing-optional" })] }) });
		const answer = requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" });
		assert.equal(answer.resultId, "result-1");
		// The explicitly missing output has no artifact row, and that is a
		// fact the retained manifest still carries.
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM output_artifacts").get().n, 1);
	} finally {
		store.close();
	}
});

test("W2929: an output answered with the wrong TYPE is refused", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			outputs: [answered("result-tree", { type: "record-output" })] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /is declared directory-result/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929 review: a result must satisfy its declared output limits", () => {
	const store = open();
	try {
		const limited = declaration({ outputs: [{
			name: "result-tree", type: "directory-result", path: "out",
			required: true,
			constraints: { ...CONSTRAINTS, max_bytes: 1 },
		}] });
		quiesced(store, { declared: limited });
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [answered("result-tree")],
		}) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity");
		assert.equal(outputRow(store), undefined,
			"an output larger than its declaration was frozen");
	} finally {
		store.close();
	}
});

test("W2929 review: the attempt input digest must name an INPUT manifest",
	() => {
		const store = open();
		try {
			// Every public operation here is valid in isolation: the wrong-kind
			// document is retained under its own digest and the attempt names that
			// digest. Freeze is the boundary that must refuse to treat a result's
			// similarly-shaped output rows as trusted input declarations.
			const wrongKind = retainManifest(store, result(), "resultManifest");
			recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
				adapterDigest: digest("adapter"),
				profileDigest: digest("profile"),
				inputDigest: wrongKind.digest, policyDigest: POLICY });
			claimed(store, ASSIGNMENT, wrongKind.digest);
			activateAssignment(store, session(),
				{ attemptId: ATTEMPT, expect: ASSIGNMENT });
			for (const value of EXECUTION_PATHS.quiescent) {
				observe(store, { attemptId: ATTEMPT,
					axis: "execution_runtime", value });
			}
			observe(store, { attemptId: ATTEMPT,
				axis: "worker_disposition", value: "completed" });
			const other = adapter({ seal: () => result({
				inputDigest: wrongKind.digest,
				outputs: [answered("result-tree")],
			}) });
			assert.throws(() => requestFreeze(store, session(), other,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(outputRow(store), undefined);
		} finally {
			store.close();
		}
	});

test("W2929: one declaration answered TWICE is not an answer", () => {
	const store = open();
	try {
		quiesced(store);
		const other = adapter({ seal: () => result({
			outputs: [answered("result-tree"), answered("result-tree")] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& /twice/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a result cannot be recorded against a declaration nobody holds",
	() => {
		const store = open();
		try {
			// The attempt names an input manifest that was never retained,
			// which is exactly the state the freeze slice shipped in.
			quiesced(store, { declared: null });
			assert.throws(() => requestFreeze(store, session(), adapter(),
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& /does not hold it/.test(error.message));
			assert.equal(outputRow(store), undefined);
		} finally {
			store.close();
		}
	});

// -- retention --------------------------------------------------------------

test("W2929: the sealed result survives, byte for byte, across a reopen", () => {
	const path = storePath();
	const first = open(path);
	let sealed;
	try {
		quiesced(first);
		sealed = result();
		requestFreeze(first, session(), adapter({ seal: () => sealed }),
			{ attemptId: ATTEMPT, disposition: "completed" });
	} finally {
		first.close();
	}
	const second = new ControlStore(path, { incarnation: "manager-2",
		clock: () => NOW });
	try {
		const digestOf = outputRow(second).manifest_digest;
		const retained = loadManifest(second, digestOf, "resultManifest");
		// EVERYTHING, not a summary: the content trees, the explicitly
		// missing outputs, the evidence and the freeze operation.
		assert.deepEqual(retained, sealed,
			"the manager kept a digest and lost the document it names");
	} finally {
		second.close();
	}
});

test("W2929: a retained manifest is never handed out as an alias", () => {
	const store = open();
	try {
		quiesced(store);
		requestFreeze(store, session(), adapter(),
			{ attemptId: ATTEMPT, disposition: "completed" });
		const key = outputRow(store).manifest_digest;
		const mine = loadManifest(store, key, "resultManifest");
		mine.result_id = "tampered";
		mine.outputs.length = 0;
		assert.equal(loadManifest(store, key, "resultManifest").result_id,
			"result-1",
			"a durable record was editable through the copy it handed out");
		assert.equal(loadManifest(store, key, "resultManifest").outputs.length, 1);
	} finally {
		store.close();
	}
});

test("W2929: retaining the same declaration twice is one row", () => {
	const store = open();
	try {
		const once = retainManifest(store, DECLARATION, "inputManifest");
		const twice = retainManifest(store, DECLARATION, "inputManifest");
		assert.equal(once.retained, true);
		assert.equal(twice.retained, false);
		assert.equal(once.digest, twice.digest);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM manifests").get().n, 1);
	} finally {
		store.close();
	}
});

test("W2929: a retained digest cannot be made to name two documents", () => {
	const store = open();
	try {
		const { digest: key } = retainManifest(store, DECLARATION,
			"inputManifest");
		// Only a hand-edited store produces this, which is exactly why it is
		// checked rather than assumed away.
		store.db.prepare("UPDATE manifests SET body = ? WHERE digest = ?")
			.run("{\"schema\":\"baton.worker-manifest/input\"}", key);
		assert.throws(() => retainManifest(store, DECLARATION, "inputManifest"),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929 review: result retention refuses an existing digest collision",
	() => {
		const store = open();
		try {
			quiesced(store);
			const sealed = result();
			store.db.prepare(
				"INSERT INTO manifests (digest, schema, body, retained_at) "
				+ "VALUES (?, ?, ?, ?)")
				.run(sealed.manifest_digest, sealed.schema, "{}", NOW);
			assert.throws(() => requestFreeze(store, session(),
				adapter({ seal: () => sealed }),
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest");
			assert.equal(outputRow(store), undefined,
				"the result row referenced bytes its digest does not identify");
		} finally {
			store.close();
		}
	});

test("W2929: an unreadable manifest is never retained", () => {
	const store = open();
	try {
		assert.throws(() => retainManifest(store, { schema: "nonsense" },
			"inputManifest"),
			(error) => error instanceof ContractError);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM manifests").get().n, 0,
			"a document this manager cannot read survived in its store");
	} finally {
		store.close();
	}
});

// -- the other side of the declared limits ----------------------------------

function limitedTo(constraints) {
	return declaration({ outputs: [{
		name: "result-tree", type: "directory-result", path: "out",
		required: true, constraints: { ...CONSTRAINTS, ...constraints } }] });
}

test("W2929: a result exceeding its declared ENTRY limit is refused", () => {
	const store = open();
	try {
		const limited = limitedTo({ max_entries: 1 });
		quiesced(store, { declared: limited });
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [{ name: "result-tree", type: "directory-result",
			            status: "present",
			            content_manifest: manifest(entries(["a.txt", "b.txt"])),
			            artifact: artifact() }] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "limit"
				&& /at most 1 entries/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a media type its declaration does not allow is refused", () => {
	const store = open();
	try {
		const limited = limitedTo({ allowed_media_types: ["application/json"] });
		quiesced(store, { declared: limited });
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [answered("result-tree")] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.category === "policy" && error.code === "denied");
	} finally {
		store.close();
	}
});

test("W2929: an EMPTY allow-list allows nothing", () => {
	const store = open();
	try {
		// The fail-open reading — "it names nothing, so everything passes" —
		// is exactly the one a rule written to close cannot have.
		const limited = limitedTo({ allowed_media_types: [] });
		quiesced(store, { declared: limited });
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [answered("result-tree")] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.code === "denied");
	} finally {
		store.close();
	}
});

test("W2929: an absent output is not measured against a size", () => {
	const store = open();
	try {
		const limited = declaration({ outputs: [{
			name: "notes", type: "record-output", path: "notes",
			required: false,
			constraints: { ...CONSTRAINTS, max_bytes: 0, max_entries: 0 } }] });
		quiesced(store, { declared: limited });
		// A missing output carries no tree and no artifact. Measuring absence
		// against a size would refuse it for being absent, which `required`
		// already decides on its own terms.
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [answered("notes", { type: "record-output",
			                              status: "missing-optional" })] }) });
		assert.equal(requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }).resultId,
			"result-1");
	} finally {
		store.close();
	}
});

// -- what a retained document must be before it is trusted ------------------

test("W2929: loading a retained manifest names the kind it must be", () => {
	const store = open();
	try {
		const { digest: key } = retainManifest(store, DECLARATION,
			"inputManifest");
		assert.throws(() => loadManifest(store, key),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "schema");
	} finally {
		store.close();
	}
});

test("W2929: a retained body that no longer recomputes to its key is refused",
	() => {
		const store = open();
		try {
			const { digest: key } = retainManifest(store, DECLARATION,
				"inputManifest");
			// A hand-edited store. The document still validates — only its
			// relationship to the key it is filed under has been broken, and
			// a guard on the way IN cannot see an edit made afterwards.
			const { manifest_digest: _was, ...edited } = DECLARATION;
			edited.manifest_id = "input-2";
			store.db.prepare("UPDATE manifests SET body = ? WHERE digest = ?")
				.run(JSON.stringify({ ...edited,
					manifest_digest: digest(edited) }), key);
			assert.throws(() => loadManifest(store, key, "inputManifest"),
				(error) => error instanceof ContractError
					&& error.code === "digest");
		} finally {
			store.close();
		}
	});

test("W2929: an output that says it is MISSING must be missing", () => {
	const store = open();
	try {
		quiesced(store, { disposition: "unable" });
		// The schema permits `missing-optional` beside an artifact, and that
		// is a document contradicting itself. Believing either half would be
		// this manager choosing which half to believe.
		const other = adapter({ seal: () => result({ disposition: "unable",
			outputs: [{
				name: "result-tree", type: "directory-result",
				status: "missing-optional", content_manifest: null,
				artifact: artifact() }] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "unable" }),
			(error) => error instanceof ContractError
				&& /a missing output is missing/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929 review: an output that says it is PRESENT must carry material",
	() => {
		const store = open();
		try {
			quiesced(store);
			// The schema deliberately leaves status/material correlation to the
			// semantic boundary. A required output with neither a tree nor an
			// artifact is not made real by spelling its status `present`.
			const other = adapter({ seal: () => result({ outputs: [{
				name: "result-tree", type: "directory-result", status: "present",
				content_manifest: null, artifact: null,
			}] }) });
			assert.throws(() => requestFreeze(store, session(), other,
				{ attemptId: ATTEMPT, disposition: "completed" }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(outputRow(store), undefined,
				"an empty required output was frozen as present");
		} finally {
			store.close();
		}
	});

test("W2929: a present output carrying only ONE representation is refused",
	() => {
		// The reviewer's case drives neither. These drive each half, because a
		// rule that only rejects the empty case is satisfied by supplying
		// whichever representation is cheaper to fake.
		for (const [what, output] of [
				["no artifact", { content_manifest: manifest(entries(["a.txt"])),
				                  artifact: null }],
				["no content manifest", { content_manifest: null,
				                          artifact: artifact() }]]) {
			const store = open();
			try {
				quiesced(store);
				const other = adapter({ seal: () => result({ outputs: [{
					name: "result-tree", type: "directory-result",
					status: "present", ...output }] }) });
				assert.throws(() => requestFreeze(store, session(), other,
					{ attemptId: ATTEMPT, disposition: "completed" }),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema"
						&& /binds both/.test(error.message), what);
				assert.equal(outputRow(store), undefined, what);
			} finally {
				store.close();
			}
		}
	});

test("W2929: the ARTIFACT's declared size is bounded too", () => {
	const store = open();
	try {
		const limited = limitedTo({ max_bytes: 20 });
		quiesced(store, { declared: limited });
		// The tree is well inside the limit; the artifact is not. Measuring
		// only the tree would leave the transported representation unbounded.
		const other = adapter({ seal: () => result({
			inputDigest: limited.manifest_digest,
			outputs: [{ name: "result-tree", type: "directory-result",
			            status: "present",
			            content_manifest: manifest(entries(["a.txt"])),
			            artifact: { ...artifact(), bytes: 4096 } }] }) });
		assert.throws(() => requestFreeze(store, session(), other,
			{ attemptId: ATTEMPT, disposition: "completed" }),
			(error) => error instanceof ContractError
				&& error.code === "limit"
				&& /its artifact carries 4096/.test(error.message));
	} finally {
		store.close();
	}
});
