// W2929 item 3, fifth slice: trusted intake and cleanup.
//
// The two rules these cases exist for are both about what the manager must
// NOT do: intake never publishes, and cleanup never changes authority state.
// A rule of that shape cannot be checked by looking at what happened — it is
// checked by driving a real authority and asserting that nothing did.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { V12Authority, V12 } from "../src/authority/index.mjs";
import { ContractError, GOLDEN_BEARER, digest }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { activateAssignment, observe, recordAttempt }
	from "../src/worker_manager/attempts.mjs";
import { destroyOperationId, intakeOf, intakeOperationId, recordIntake,
         requestDestroy, settleCleanup }
	from "../src/worker_manager/intake.mjs";
import { retainManifest } from "../src/worker_manager/manifests.mjs";
import { freezeOperation, requestFreeze }
	from "../src/worker_manager/output.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const WHO = "poc.claude";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const ASSIGNMENT = { authorityUuid: UUID, workId: WORK, participant: WHO,
                     generation: 1 };
const LOCATOR = "artifact://store/mount-1";

function storePath() {
	return join(ownedTemp("v12-manager-"), "control.sqlite3");
}

function open(path = storePath()) {
	return new ControlStore(path, { incarnation: "manager-1",
		clock: () => NOW });
}

/** The session. Cleanup reads through it and writes nothing, so the double
 *  answers one question and would notice if it were asked another. */
function session({ assignment = null, participant = WHO } = {}) {
	const calls = [];
	return {
		calls,
		participant,
		assignmentOf(workId) { calls.push(["assignmentOf", workId]);
		                       return assignment; },
	};
}

function adapter({ destroy = null } = {}) {
	const calls = [];
	return {
		calls,
		destroy(operands) {
			calls.push(["destroy", operands]);
			return destroy === null ? { destroyed: "requested" }
			                        : destroy(operands);
		},
	};
}

function claimed(store, assignment = ASSIGNMENT) {
	store.db.prepare(
		"INSERT INTO offers (offer_id, work_id, authority_uuid, participant, "
		+ "runtime_attempt_id, incarnation, input_digest, policy_digest, "
		+ "profile_digest, verifier, verifier_spent, issued_at, expires_at, "
		+ "state, claim_generation) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, "
		+ "?, ?, 'claimed', ?)")
		.run(`offer-for-${assignment.workId}-${assignment.generation}`,
		     assignment.workId, assignment.authorityUuid,
		     assignment.participant, ATTEMPT, "manager-1", digest("input"),
		     digest("policy"), digest("profile"), `sha256:${"0".repeat(64)}`,
		     NOW, "2026-08-22T13:00:00.000Z", assignment.generation);
}

// THE REAL MATERIAL, through the real freeze path. Review [P1]: the first
// version of this fixture created no output row at all, so every positive
// intake case decided the fate of material that did not exist. A locator is
// not material.
const POLICY = digest("policy");
const CONSTRAINTS = { max_bytes: 1048576, max_entries: 1000,
                      allowed_media_types: ["application/zip"],
                      link_policy: "forbid", validator_digest: null };

function entries(paths) {
	return paths.map((path) => ({ path, bytes: path.length,
	                              content_digest: digest(path) }));
}

function manifest(list) {
	return { entries: list, entry_count: list.length,
	         total_bytes: list.reduce((sum, e) => sum + e.bytes, 0),
	         tree_digest: digest(list) };
}

function artifact(id = "artifact-1") {
	return { artifact_id: id, media_type: "application/zip", bytes: 12,
	         content_digest: digest(id), locator: `artifact://store/${id}` };
}

function sealedDocument(body) {
	return { ...body, manifest_digest: digest(body) };
}

const DECLARATION = sealedDocument({
	version: { major: 1, minor: 0 }, manifest_id: "input-1", created_at: NOW,
	extensions: {}, schema: "baton.worker-manifest/input",
	work_ref: { authority_uuid: UUID, work_id: WORK },
	assignment_contract: "v12-assignment-1",
	human_contract: artifact("contract-1"),
	sources: [{ name: "source", type: "directory",
	            uri: "artifact://store/source-1", destination: "in",
	            required: true, content_manifest: manifest(entries(["seed.txt"])) }],
	outputs: [{ name: "result-tree", type: "directory-result", path: "out",
	            required: true, constraints: CONSTRAINTS }],
	role_instructions_digest: digest("role"), policy_digest: POLICY,
	toolchain_digest: digest("toolchain"), worker_image_digest: digest("image"),
	runtime_profile_digest: digest("profile"),
	resource_policy_digest: digest("resource"),
	network_policy_digest: digest("network"), mount_policy_digest: digest("mount"),
	tool_policy_digest: digest("tool"), credential_policy_digest: digest("credential"),
	retention_policy_digest: digest("retention"),
	record_binding: { root: "work", path: "records/f/PLAN.md",
	                  finding_digest: digest("finding"), plan_digest: digest("plan") },
});
const INPUT = DECLARATION.manifest_digest;

function resultFor(assignment, freeze) {
	return sealedDocument({
		version: { major: 1, minor: 0 }, manifest_id: "manifest-1",
		created_at: NOW, extensions: {},
		schema: "baton.worker-manifest/result", result_id: "result-1",
		assignment_ref: {
			work_ref: { authority_uuid: assignment.authorityUuid,
			            work_id: assignment.workId },
			participant: assignment.participant,
			generation: assignment.generation },
		input_manifest_digest: INPUT, policy_digest: POLICY,
		disposition: "completed",
		outputs: [{ name: "result-tree", type: "directory-result",
		            status: "present",
		            content_manifest: manifest(entries(["a.txt"])),
		            artifact: artifact() }],
		evidence: [], freeze_operation: freeze, manager_observed_at: NOW,
	});
}

/** An attempt whose assignment is fixed and whose runtime has been attached
 *  and then stopped — the state cleanup finds. */
function ended(store, { assignment = ASSIGNMENT, api = null,
                        execution = "quiescent", material = true } = {}) {
	retainManifest(store, DECLARATION, "inputManifest");
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile"),
		inputDigest: INPUT, policyDigest: POLICY });
	claimed(store, assignment);
	activateAssignment(store, api ?? session({ assignment }),
		{ attemptId: ATTEMPT, expect: assignment });
	for (const value of TO_QUIESCENT) {
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime", value });
	}
	if (material) {
		observe(store, { attemptId: ATTEMPT, axis: "worker_disposition",
			value: "completed" });
		// The REAL freeze, so the intake decision names a result this manager
		// actually sealed. The freeze needs the assignment live; cleanup needs
		// it over, so the fixture's session answers live only here.
		requestFreeze(store, session({ assignment }),
			{ seal: ({ operation }) => resultFor(assignment, operation) },
			{ attemptId: ATTEMPT, disposition: "completed" });
	}
	for (const value of AFTER_FREEZE[execution]) {
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime", value });
	}
	return ATTEMPT;
}

// The route to quiescence, and then anything further the case wants after the
// material has been frozen.
const TO_QUIESCENT = Object.freeze(["start-requested", "running", "quiescent"]);
// What the case wants AFTER the material has been frozen, which is why
// `quiescent` adds nothing: the fixture is already there.
const AFTER_FREEZE = Object.freeze({ quiescent: [], destroyed: ["destroyed"] });

function row(store) {
	return store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id=?").get(ATTEMPT);
}

function decide(store, overrides = {}) {
	return recordIntake(store, { attemptId: ATTEMPT, disposition: "accepted",
		retention: "retained", locator: LOCATOR, ...overrides });
}

// -- the trusted intake decision --------------------------------------------

test("W2929: an intake decision is recorded and nothing else moves", () => {
	const store = open();
	try {
		ended(store);
		const before = row(store);
		const answer = decide(store, { disposition: "rejected",
			retention: "quarantined", reason: "superseded" });
		assert.equal(answer.disposition, "rejected");
		assert.equal(answer.retention, "quarantined");
		const stored = intakeOf(store, row(store));
		assert.equal(stored.disposition, "rejected");
		assert.equal(stored.retention, "quarantined");
		assert.equal(stored.locator, LOCATOR);
		assert.equal(stored.generation, 1);
		// NOT ONE AXIS. Intake changes only its own disposition, and the ten
		// axes are the manager's observations rather than intake's.
		for (const axis of ["consent_runtime", "execution_runtime", "output",
		                    "worker_disposition", "proposal", "verification",
		                    "technical_review", "approval", "integration",
		                    "cleanup"]) {
			assert.equal(row(store)[axis], before[axis], axis);
		}
	} finally {
		store.close();
	}
});

test("W2929: RETENTION IS NOT ACCEPTANCE", () => {
	const store = open();
	try {
		ended(store);
		// A rejected draft that is retained under policy is an ordinary
		// outcome. Collapsing the two facts would make it unsayable.
		decide(store, { disposition: "rejected", retention: "retained" });
		const stored = intakeOf(store, row(store));
		assert.equal(stored.disposition, "rejected");
		assert.equal(stored.retention, "retained");
	} finally {
		store.close();
	}
});

test("W2929: the same decision replays and a DIFFERENT one collides", () => {
	const store = open();
	try {
		ended(store);
		const first = decide(store);
		assert.deepEqual(decide(store), first, "the repeat was re-derived");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 1);
		// "Each receives a deliberate decision" means ONE decision, not the
		// last one written.
		assert.throws(() => decide(store, { disposition: "rejected" }),
			(error) => error instanceof ContractError
				&& error.code === "operation-collision");
		assert.equal(intakeOf(store, row(store)).disposition, "accepted");
	} finally {
		store.close();
	}
});

test("W2929 re-review: intake replay precedes current output state", () => {
	const store = open();
	try {
		ended(store);
		const first = decide(store);
		// Intake now owns the exact result digest and keeps its retained bytes
		// alive through a foreign key. The outputs row is current indexing state,
		// not part of whether the already-committed intake operation happened.
		store.db.prepare(
			"DELETE FROM output_artifacts WHERE runtime_attempt_id = ?")
			.run(ATTEMPT);
		store.db.prepare("DELETE FROM outputs WHERE runtime_attempt_id = ?")
			.run(ATTEMPT);
		assert.deepEqual(decide(store), first,
			"an exact intake retry was re-derived from current output state");
		assert.throws(() => decide(store, { disposition: "rejected" }),
			(error) => error instanceof ContractError
				&& error.code === "operation-collision");
	} finally {
		store.close();
	}
});

test("W2929: only the pinned intake and retention words are accepted", () => {
	const store = open();
	try {
		ended(store);
		for (const overrides of [{ disposition: "maybe" },
		                         { retention: "deleted" }]) {
			assert.throws(() => decide(store, overrides),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema", JSON.stringify(overrides));
		}
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: a retention locator carrying a credential never lands", () => {
	const store = open();
	try {
		ended(store);
		assert.throws(() => decide(store,
			{ locator: "https://user:secret@store/mount-1" }),
			(error) => error instanceof ContractError);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929: an intake decision belongs to an exact generation", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		// A decision read under a different generation is a decision about
		// something else, and saying nothing would be worse than refusing.
		store.db.prepare("UPDATE intake SET generation = 2 "
			+ "WHERE runtime_attempt_id = ?").run(ATTEMPT);
		assert.throws(() => intakeOf(store, row(store)),
			(error) => error instanceof ContractError
				&& error.category === "stale-assignment");
	} finally {
		store.close();
	}
});

test("W2929: an unactivated attempt has no generation to decide under", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.throws(() => decide(store),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

test("W2929 review: intake cannot decide before material is sealed", () => {
	const store = open();
	try {
		ended(store, { material: false });
		// The attempt is assigned and quiescent, but it has no output row and
		// no immutable result manifest. Intake decides the fate of material;
		// without material there is no object to accept, reject or retain.
		assert.throws(() => decide(store),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: intake prose cannot persist a live bearer", () => {
	const store = open();
	try {
		ended(store);
		assert.throws(() => decide(store, { reason: GOLDEN_BEARER }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "secret-leak");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: a retention deadline is a validated timestamp", () => {
	const store = open();
	try {
		ended(store);
		assert.throws(() => decide(store, { retainUntil: "tomorrow" }),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM intake").get().n, 0);
	} finally {
		store.close();
	}
});

// -- cleanup ----------------------------------------------------------------

test("W2929: cleanup BLOCKS ON INTAKE, durably", () => {
	const store = open();
	try {
		ended(store);
		const runtime = adapter();
		const blocked = destroyOperationId(store, row(store));
		assert.throws(() => requestDestroy(store, session(), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& /no recorded intake decision/.test(error.message));
		assert.equal(runtime.calls.length, 0,
			"the runtime was destroyed before intake had decided");
		assert.equal(row(store).cleanup, "blocked-on-intake");
		// DURABLE TO ITS OWN OPERATION: the retry replays the refusal rather
		// than re-deriving it, so the store can be asked what happened.
		assert.equal(store.db.prepare(
			"SELECT state FROM operations WHERE operation_id = ?")
			.get(blocked).state, "refused");
		assert.throws(() => requestDestroy(store, session(), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error.replayed === true);
	} finally {
		store.close();
	}
});

test("W2929: a later re-evaluation is a NEW operation", () => {
	const store = open();
	try {
		ended(store);
		const blocked = destroyOperationId(store, row(store));
		assert.throws(() => requestDestroy(store, session(), adapter(),
			{ attemptId: ATTEMPT }), () => true);
		decide(store);
		const after = destroyOperationId(store, row(store));
		assert.notEqual(after, blocked,
			"the re-evaluation reused the identity its refusal is durable to");
		const runtime = adapter();
		const answer = requestDestroy(store, session(), runtime,
			{ attemptId: ATTEMPT });
		assert.equal(answer.ordered, true);
		assert.equal(runtime.calls.length, 1);
	} finally {
		store.close();
	}
});

test("W2929: cleanup waits for the assignment to be over", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		const runtime = adapter();
		// Still live at the authority. Destroying its runtime would tear out
		// a worker that is still authorized to be working.
		assert.throws(() => requestDestroy(store,
			session({ assignment: ASSIGNMENT }), runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& /still live/.test(error.message));
		assert.equal(runtime.calls.length, 0);
	} finally {
		store.close();
	}
});

test("W2929: ordering destruction is not evidence the runtime is gone", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		const answer = requestDestroy(store, session(), adapter(),
			{ attemptId: ATTEMPT });
		// The adapter accepted the order. That is not the runtime being gone,
		// and positive absence is item 4's question.
		assert.deepEqual(answer.settlement, { destroyed: "requested" });
		assert.equal(answer.cleanup, "pending");
		assert.equal(row(store).cleanup, "pending");
	} finally {
		store.close();
	}
});

test("W2929: cleanup COMPLETES on a positive destroyed observation", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		requestDestroy(store, session(), adapter(), { attemptId: ATTEMPT });
		observe(store, { attemptId: ATTEMPT, axis: "execution_runtime",
			value: "destroyed", source: { incarnation: "adapter-1", seq: 1 } });
		assert.equal(settleCleanup(store, ATTEMPT).cleanup, "complete");
		assert.equal(row(store).cleanup, "complete");
	} finally {
		store.close();
	}
});

test("W2929 review: a destroyed runtime does not bypass intake", () => {
	const store = open();
	try {
		ended(store, { execution: "destroyed" });
		// A runtime observation proves absence, not that trusted intake made a
		// decision about the material that may now be disposed.
		assert.throws(() => settleCleanup(store, ATTEMPT),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
		assert.notEqual(row(store).cleanup, "complete");
	} finally {
		store.close();
	}
});

test("W2929: the adapter is told which act it is settling", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		const runtime = adapter();
		const operationId = destroyOperationId(store, row(store));
		requestDestroy(store, session(), runtime, { attemptId: ATTEMPT });
		const [, operands] = runtime.calls.find(([what]) => what === "destroy");
		assert.equal(operands.operationId, operationId);
		assert.deepEqual(operands.assignment, ASSIGNMENT);
	} finally {
		store.close();
	}
});

test("W2929: an adapter without destroy() is refused before anything moves",
	() => {
		const store = open();
		try {
			ended(store);
			decide(store);
			assert.throws(() => requestDestroy(store, session(), {},
				{ attemptId: ATTEMPT }),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "schema");
			assert.equal(row(store).cleanup, "pending");
		} finally {
			store.close();
		}
	});

// -- against a real authority -----------------------------------------------

test("W2929: intake and cleanup change NO authority state", () => {
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
		ended(store, { assignment, api });
		api.cancel({ expect: assignment, operationId: "cancel-1",
			reason: "operator" });
		const before = api.projectWork(WORK);
		recordIntake(store, { attemptId: ATTEMPT, disposition: "rejected",
			retention: "quarantined", locator: LOCATOR });
		requestDestroy(store, api, adapter(), { attemptId: ATTEMPT });
		const after = api.projectWork(WORK);
		// EVERY field the projection carries, not a chosen few: "changes no
		// authority state" is a claim about all of it.
		assert.deepEqual({ ...after }, { ...before },
			"intake or cleanup moved authority state");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: a real live assignment blocks destruction", () => {
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
		ended(store, { assignment, api });
		recordIntake(store, { attemptId: ATTEMPT, disposition: "accepted",
			retention: "retained", locator: LOCATOR });
		const runtime = adapter();
		assert.throws(() => requestDestroy(store, api, runtime,
			{ attemptId: ATTEMPT }),
			(error) => error instanceof ContractError
				&& /still live/.test(error.message));
		assert.equal(runtime.calls.length, 0);
	} finally {
		store.close();
		authority.dispose();
	}
});

// -- the other side of each correction --------------------------------------

test("W2929: the decision names the exact result it judged", () => {
	const store = open();
	try {
		ended(store);
		const answer = decide(store);
		const sealed = store.db.prepare(
			"SELECT manifest_digest FROM outputs WHERE runtime_attempt_id=?")
			.get(ATTEMPT).manifest_digest;
		assert.equal(answer.resultDigest, sealed);
		assert.equal(intakeOf(store, row(store)).result_digest, sealed);
		// And the bytes it names are still there to be read, which is the
		// whole point of naming them rather than a locator.
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM manifests WHERE digest = ?")
			.get(sealed).n, 1);
	} finally {
		store.close();
	}
});

test("W2929 re-review: the stored decision stays bound to its exact result", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		// A foreign key proves only that SOME retained manifest exists. Put a
		// second, individually valid result in that table and point intake at it:
		// the committed decision still identifies the first result, not this one.
		const { manifest_digest: _old, ...body } = resultFor(ASSIGNMENT,
			freezeOperation(row(store)));
		const alternate = sealedDocument({ ...body,
			manifest_id: "manifest-2", result_id: "result-2" });
		retainManifest(store, alternate, "resultManifest");
		store.db.prepare("UPDATE intake SET result_digest = ? "
			+ "WHERE runtime_attempt_id = ?")
			.run(alternate.manifest_digest, ATTEMPT);
		assert.throws(() => intakeOf(store, row(store)),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "digest");
	} finally {
		store.close();
	}
});

test("W2929 re-review: every stored intake operand is authenticated", () => {
	for (const [column, changed] of [
		["disposition", "rejected"],
		["retention", "quarantined"],
		["locator", "artifact://store/another-mount"],
		["retain_until", "2026-09-01T00:00:00.000Z"],
		["reason", "changed after commit"],
	]) {
		const store = open();
		try {
			ended(store);
			decide(store);
			store.db.prepare(`UPDATE intake SET ${column} = ? `
				+ "WHERE runtime_attempt_id = ?").run(changed, ATTEMPT);
			assert.throws(() => intakeOf(store, row(store)),
				(error) => error instanceof ContractError
					&& error.category === "integrity"
					&& error.code === "digest", column);
		} finally {
			store.close();
		}
	}
});

test("W2929: a bearer in ANY durable intake column is refused", () => {
	for (const field of ["reason", "locator"]) {
		const store = open();
		try {
			ended(store);
			const carrier = field === "locator"
				? `artifact://store/${GOLDEN_BEARER}` : GOLDEN_BEARER;
			assert.throws(() => decide(store, { [field]: carrier }),
				(error) => error instanceof ContractError, field);
			assert.equal(store.db.prepare(
				"SELECT COUNT(*) AS n FROM intake").get().n, 0, field);
		} finally {
			store.close();
		}
	}
});

test("W2929: a well-formed deadline is kept verbatim", () => {
	const store = open();
	try {
		ended(store);
		// The other side of the deadline rule: refusing prose must not also
		// refuse a deadline.
		const answer = decide(store,
			{ retainUntil: "2026-09-01T00:00:00.000Z" });
		assert.equal(answer.retainUntil, "2026-09-01T00:00:00.000Z");
		assert.equal(intakeOf(store, row(store)).retain_until,
			"2026-09-01T00:00:00.000Z");
	} finally {
		store.close();
	}
});

test("W2929: absence and policy are two separate gates", () => {
	const store = open();
	try {
		ended(store, { execution: "destroyed" });
		// With intake decided, the destroyed runtime completes cleanup — so
		// the refusal above is the POLICY gate and not a second absence gate.
		decide(store);
		assert.equal(settleCleanup(store, ATTEMPT).cleanup, "complete");
		assert.equal(row(store).cleanup, "complete");
	} finally {
		store.close();
	}
});

test("W2929: a CHANGED decision collides after the output index is gone", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		// The other side of the replay ordering. The reviewer's case pins the
		// exact retry; this pins that a different one still COLLIDES rather
		// than being hidden behind the same precondition.
		store.db.prepare(
			"DELETE FROM output_artifacts WHERE runtime_attempt_id = ?")
			.run(ATTEMPT);
		store.db.prepare("DELETE FROM outputs WHERE runtime_attempt_id = ?")
			.run(ATTEMPT);
		assert.throws(() => decide(store, { disposition: "rejected" }),
			(error) => error instanceof ContractError
				&& error.code === "operation-collision");
		assert.equal(intakeOf(store, row(store)).disposition, "accepted");
	} finally {
		store.close();
	}
});

test("W2929: an intake row with no committed decision is refused", () => {
	const store = open();
	try {
		ended(store);
		decide(store);
		// The journal is the witness, so removing it leaves a row nothing
		// authenticates — the same fabricated-durable-state shape as pointing
		// the row at another result, arriving from the other side.
		store.db.prepare("DELETE FROM operations WHERE operation_id = ?")
			.run(intakeOperationId(row(store)));
		assert.throws(() => intakeOf(store, row(store)),
			(error) => error instanceof ContractError
				&& error.category === "integrity" && error.code === "digest"
				&& /no committed decision/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a decision naming a non-result manifest is refused, TWICE OVER",
	() => {
	const store = open();
	try {
		ended(store);
		decide(store);
		// The foreign key admits any retained manifest. An INPUT manifest is
		// a perfectly valid thing to hold, and it is not a result.
		//
		// Measured: TWO independent guards refuse this, and removing either
		// alone leaves the other covering it. The signature authentication
		// catches the changed digest; the typed load catches the wrong kind.
		// Only a mutation that removes both makes this case fail, which is
		// recorded rather than presented as one guard being witnessed.
		const inputDigest = row(store).input_digest;
		store.db.prepare("UPDATE intake SET result_digest = ? "
			+ "WHERE runtime_attempt_id = ?").run(inputDigest, ATTEMPT);
		assert.throws(() => intakeOf(store, row(store)),
			(error) => error instanceof ContractError);
	} finally {
		store.close();
	}
});
