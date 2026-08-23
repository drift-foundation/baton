// W2929 plan item 3, fifth slice: TRUSTED INTAKE AND CLEANUP.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance:
//
//   "Ended-assignment material is sealed/quarantined. Intake changes only its
//    trusted disposition and never publishes on the dead generation.
//    Destruction waits for the recorded intake/discard policy; cleanup never
//    changes authority state."
//
// and from the contract, SPEC 6.4:
//
//   `output.retain`  -> "retained/quarantined locator and deadline; retention
//                        is not acceptance"
//   `runtime.destroy`-> "collection/intake boundary satisfied or pinned
//                        discard policy ... cleanup observation only; never
//                        changes authority state"
//
// TWO DESIGN CONSEQUENCES WORTH STATING BEFORE THE CODE.
//
// `recordIntake` IS NOT GIVEN A SESSION. "Never publishes on the dead
// generation" is a rule about what intake may do, and the strongest way to
// keep it is to hand this boundary no way to reach the authority at all. A
// handle that is passed and not used is a rule enforced by good intentions.
//
// THE DISCARD PATH IS CLOSED. SPEC 6.4 admits destruction under a "pinned
// discard policy" as well as a satisfied intake boundary, but a policy this
// function takes as an argument is the rejected `absenceProven` shape: a
// proof the caller writes is not a proof. Until a discard policy is a durable
// fact this manager can read, destruction requires a recorded intake
// decision, and the refusal names what would open it.

import { assertNoDurableSecret, ContractError, digest,
         validateSchemaFragment, validateUri } from "./contracts.mjs";
import { observe } from "./attempts.mjs";
import { loadManifest } from "./manifests.mjs";

const INTAKE_DISPOSITIONS = Object.freeze(["accepted", "rejected"]);
const RETENTIONS = Object.freeze(["retained", "quarantined"]);

function attemptOf(store, attemptId) {
	const row = store.db.prepare(
		"SELECT * FROM attempts WHERE runtime_attempt_id = ?").get(attemptId);
	if (row === undefined) {
		throw new ContractError("refused", "precondition",
			`no runtime attempt ${attemptId}`);
	}
	return row;
}

function fixedAssignment(attempt) {
	if (attempt.assignment_generation === null) return null;
	return { authorityUuid: attempt.authority_uuid, workId: attempt.work_id,
	         participant: attempt.assignment_participant,
	         generation: attempt.assignment_generation };
}

function requireAssignment(attempt, what) {
	const expect = fixedAssignment(attempt);
	if (expect === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attempt.runtime_attempt_id} has no fixed assignment; `
			+ `${what} belongs to an exact generation and there is none`);
	}
	return expect;
}

/** The ONE intake decision for an attempt's exact generation. */
export function intakeOperationId(attempt) {
	return `intake.decide:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
	}).slice("sha256:".length)}`;
}

/** The trusted intake decision, recorded — and nothing else.
 *
 *  Every draft receives a DELIBERATE decision before retention or disposal,
 *  and intake may reject all of them. What it may never do is publish: this
 *  writes one row, moves no axis, and cannot reach the authority because it
 *  was never given a way to.
 *
 *  ONE DECISION PER ATTEMPT. An exact repeat replays; a different decision
 *  under the same identity is an operation collision, because "each receives
 *  a deliberate decision" means one decision, not the last one written. */
export function recordIntake(store, { attemptId, disposition, retention,
                                      locator, retainUntil = null,
                                      reason = null }) {
	const attempt = attemptOf(store, attemptId);
	const expect = requireAssignment(attempt, "an intake decision");
	if (!INTAKE_DISPOSITIONS.includes(disposition)) {
		throw new ContractError("integrity", "schema",
			`${disposition} is not an intake disposition; intake accepts or `
			+ `rejects, and each draft receives one deliberate decision`);
	}
	if (!RETENTIONS.includes(retention)) {
		throw new ContractError("integrity", "schema",
			`${retention} is not a retention; material is retained or `
			+ `quarantined, and RETENTION IS NOT ACCEPTANCE`);
	}
	// The locator is a durable reference like any other: absolute, and
	// carrying no credential. `validateUri` is the same rule the manifest
	// entry applies to artifact locators, for the same reason.
	validateUri(locator, `attempt ${attemptId} retention locator`);
	// A DEADLINE IS A TIMESTAMP. Review [P2]: the interface and the contract
	// both call this a deadline and the STRICT column constrained only its
	// storage class, so the literal `tomorrow` was accepted as durable
	// scheduling state. No expiry policy is decided here; a deadline is
	// simply a deadline or it is not one.
	if (retainUntil !== null) {
		validateSchemaFragment(retainUntil, "timestamp",
			`attempt ${attemptId} retention deadline`);
	}
	// THE COMMITTED DECISION FIRST, and only then today's output index.
	//
	// Review [P1]: the sealed-output read ran ahead of the journal, so once
	// the decision owned the result digest and kept its manifest alive,
	// dropping the now-redundant `outputs` row turned an exact retry into a
	// precondition failure and hid a changed one instead of colliding. Same
	// rule as the output slice, in a fourth module: what a fixed identity
	// already settled is a fact about that identity.
	//
	// An existing decision already NAMES its material, so the index is only
	// consulted when there is no decision to replay — which is exactly when
	// nothing can be hidden by requiring it.
	const existing = intakeOf(store, attempt);
	let resultDigest;
	if (existing !== null) {
		resultDigest = existing.result_digest;
	} else {
		// WHICH MATERIAL IS BEING JUDGED. Review [P1]: intake required only a
		// fixed assignment and stored an unbound locator, so an attempt with
		// no sealed output at all could be accepted or rejected and a restart
		// could not prove which immutable result the decision concerned.
		// Intake decides the fate of material; without material there is
		// nothing to decide.
		const sealed = store.db.prepare(
			"SELECT * FROM outputs WHERE runtime_attempt_id = ?").get(attemptId);
		if (sealed === undefined) {
			throw new ContractError("refused", "precondition",
				`attempt ${attemptId} has no sealed output; intake decides the `
				+ `fate of material, and the quarantine manifest for material `
				+ `with no frozen result is not implemented`);
		}
		resultDigest = sealed.manifest_digest;
	}
	const operationId = intakeOperationId(attempt);
	// THROUGH THE SAME BUILDER THE READER USES. The sign-off noted that
	// "writer and reader build the record in one place" was not literal —
	// the writer assembled its own operand object beside `intakeRecord`. It
	// was true of the signature FORMULA and not of the code, and a claim that
	// is only true of the formula is one an edit can quietly falsify. The
	// writer's operands are the reader's function now, applied to the row it
	// is about to write.
	const record = intakeRecord({
		runtime_attempt_id: attemptId, result_digest: resultDigest,
		disposition, retention, locator, retain_until: retainUntil, reason,
		work_id: expect.workId, authority_uuid: expect.authorityUuid,
		participant: expect.participant, generation: expect.generation,
	});
	// THE EXACT DURABLE ROW, before any of it is written. Review [P1]: the
	// transaction guard scans the serialized RESULT, and the result omitted
	// `reason` — so a live bearer passed as prose committed verbatim. A
	// summary that omits a column is not a guard over that column.
	assertNoDurableSecret(record, `attempt ${attemptId} intake record`);
	const signature = digest({ kind: "intake.decide", operands: record });
	return store.transact(operationId, "intake.decide", signature, (db) => {
		db.prepare(
			"INSERT INTO intake (runtime_attempt_id, result_digest, "
			+ "disposition, retention, locator, retain_until, reason, "
			+ "work_id, authority_uuid, participant, generation, decided_at) "
			+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
			.run(attemptId, record.result_digest, disposition, retention,
			     locator, retainUntil, reason, expect.workId,
			     expect.authorityUuid, expect.participant, expect.generation,
			     store.clock());
		return { attemptId, resultDigest: record.result_digest, disposition,
		         retention, locator, retainUntil };
	});
}

/** The exact durable record a decision is, assembled from one place.
 *
 *  Both `recordIntake` and `intakeOf` call THIS, so the signature that COMMITS
 *  a decision and the signature that AUTHENTICATES the stored row are one
 *  computation rather than two that happen to agree today. Adding a column
 *  here changes both sides or neither. */
function intakeRecord(row) {
	return {
		runtime_attempt_id: row.runtime_attempt_id,
		result_digest: row.result_digest, disposition: row.disposition,
		retention: row.retention, locator: row.locator,
		retain_until: row.retain_until, reason: row.reason,
		work_id: row.work_id, authority_uuid: row.authority_uuid,
		participant: row.participant, generation: row.generation,
	};
}

/** THIS attempt's recorded intake decision, or null.
 *
 *  Bound to the assignment it was decided under, because a decision read
 *  under a different generation is a decision about something else. */
export function intakeOf(store, attempt) {
	const row = store.db.prepare(
		"SELECT * FROM intake WHERE runtime_attempt_id = ?")
		.get(attempt.runtime_attempt_id);
	if (row === undefined) return null;
	const expect = fixedAssignment(attempt);
	if (row.work_id !== expect?.workId
			|| row.authority_uuid !== expect?.authorityUuid
			|| row.participant !== expect?.participant
			|| row.generation !== expect?.generation) {
		// The DECIDING guard is the signature comparison below, which covers
		// these fields too. This one exists to give the common case its
		// precise portable meaning — a decision for a different generation is
		// a stale assignment, not an unauthenticated row.
		throw new ContractError("stale-assignment", "generation",
			`attempt ${attempt.runtime_attempt_id} carries an intake decision `
			+ `for a different assignment`);
	}
	// THE JOURNAL AUTHENTICATES THE ROW.
	//
	// Review [P1]: this validated the assignment fields and returned every
	// other column as trusted. The foreign key proves that SOME retained
	// manifest exists; it does not prove this is the result the decision
	// COMMITTED, so pointing the row at a second individually valid result
	// passed every check and was accepted by cleanup and by the operation
	// identity derived from it. The committed signature is the independent
	// durable witness, and it is available even when the current `outputs`
	// index is not.
	const operationId = intakeOperationId(attempt);
	const signature = digest({ kind: "intake.decide",
	                           operands: intakeRecord(row) });
	let settled;
	try {
		settled = store.replay(operationId, signature);
	} catch (failure) {
		if (failure instanceof ContractError
				&& failure.code === "operation-collision") {
			// Not a caller reusing an identity — a ROW disagreeing with the
			// decision its own operation committed. Saying `collision` would
			// hand that a portable meaning belonging to something else.
			throw new ContractError("integrity", "digest",
				`attempt ${attempt.runtime_attempt_id} carries an intake row `
				+ `the decision its operation committed does not describe`);
		}
		throw failure;
	}
	if (!settled.found) {
		throw new ContractError("integrity", "digest",
			`attempt ${attempt.runtime_attempt_id} carries an intake row with `
			+ `no committed decision behind it`);
	}
	// And the result it names must still BE a result under that key.
	loadManifest(store, row.result_digest, "resultManifest",
		`attempt ${attempt.runtime_attempt_id} intake result`);
	return row;
}

/** The cleanup operation for an attempt, DERIVED FROM THE INTAKE STATE IT
 *  WAS EVALUATED AGAINST.
 *
 *  This is what makes "the `blocked-on-intake` refusal is durable to its own
 *  operation; a later re-evaluation uses a new operation" true rather than
 *  aspirational. A retry while nothing has changed lands on the same identity
 *  and replays the same refusal; once intake decides, the identity moves, and
 *  the new evaluation is a new act.
 *
 *  A counter would have worked too, and would have been caller-authored. The
 *  evaluation is keyed on the DURABLE FACT whose change makes re-evaluating
 *  legitimate. */
export function destroyOperationId(store, attempt) {
	const decided = intakeOf(store, attempt);
	return `cleanup.destroy:${digest({
		attemptId: attempt.runtime_attempt_id,
		assignment: fixedAssignment(attempt),
		intake: decided === null ? null : {
			disposition: decided.disposition, retention: decided.retention,
			locator: decided.locator, decidedAt: decided.decided_at },
	}).slice("sha256:".length)}`;
}

/** Cleanup: order the runtime destroyed, and record a cleanup observation
 *  ONLY.
 *
 *  Never changes authority state. It is given a session so it can READ
 *  whether the assignment has ended — destruction waits for a fenced
 *  assignment — and reading is the only thing it does with one. */
export function requestDestroy(store, session, adapter, { attemptId }) {
	if (typeof adapter?.destroy !== "function") {
		throw new ContractError("integrity", "schema",
			"the runtime adapter must supply destroy(); cleanup exists to "
			+ "order it and record what came back");
	}
	const attempt = attemptOf(store, attemptId);
	const expect = requireAssignment(attempt, "cleanup");
	// THE ASSIGNMENT MUST BE OVER. Destroying the runtime of an assignment
	// the authority still believes is executing is the cancellation ordering
	// defect from the other end: the manager would tear out a worker that is
	// still authorized to be working.
	const live = session.assignmentOf(expect.workId);
	if (live !== null && live.workId === expect.workId
			&& live.authorityUuid === expect.authorityUuid
			&& live.participant === expect.participant
			&& live.generation === expect.generation) {
		throw new ContractError("refused", "precondition",
			`${expect.workId} generation ${expect.generation} is still live; `
			+ `destruction waits for the assignment to be ended or fenced`);
	}
	const operationId = destroyOperationId(store, attempt);
	const decided = intakeOf(store, attempt);
	const signature = digest({ kind: "cleanup.destroy",
	                           operands: { attemptId, expect, operationId } });
	const answer = store.transact(operationId, "cleanup.destroy", signature,
		() => {
			if (decided === null) {
				// THE AXIS MOVES AND THE REFUSAL IS DURABLE. A refusal that
				// vanished on retry would be re-derived every time and would
				// never be a fact the store can be asked about; a refusal
				// that is durable to an identity derived from the intake
				// state is one this manager can replay and a later decision
				// can supersede.
				observe(store, { attemptId, axis: "cleanup",
				                 value: "blocked-on-intake" });
				const refusal = new ContractError("refused", "precondition",
					`attempt ${attemptId} has no recorded intake decision; `
					+ `destruction waits for one, and the pinned discard `
					+ `policy that would also open it is not yet a durable `
					+ `fact this manager can read`);
				refusal.durable = true;
				throw refusal;
			}
			return { attemptId, ordered: true, intake: decided.disposition,
			         retention: decided.retention };
		});
	// ORDERED, NOT DONE — the cancellation slice's rule, and cleanup has the
	// same shape. The settlement is passed through as the adapter gave it,
	// and the cleanup axis moves only on the durable observation that the
	// runtime is actually gone.
	const settlement = adapter.destroy({ attemptId, assignment: expect,
	                                     runtimeId: attempt.runtime_id,
	                                     operationId });
	return { ...answer, settlement, ...settleCleanup(store, attemptId) };
}

/** The cleanup axis, from durable evidence and nothing else.
 *
 *  `complete` requires a positive `destroyed` observation of the runtime. An
 *  adapter that returned from `destroy()` has told this manager that it
 *  accepted the order, which is not the same as the runtime being gone —
 *  positive absence is item 4's certified-adapter question and is still
 *  closed. Until such an observation lands, cleanup stays where it is. */
export function settleCleanup(store, attemptId) {
	const attempt = attemptOf(store, attemptId);
	// THE POLICY GATE FIRST. Review [P1]: this consulted only the runtime
	// observation, so positive absence completed cleanup with no intake
	// decision at all. An observation proves the runtime is GONE; it says
	// nothing about whether the ended assignment's material was retained or
	// quarantined, and those are the two questions cleanup is specified to
	// respect. Absence does not decide policy.
	if (intakeOf(store, attempt) === null) {
		throw new ContractError("refused", "precondition",
			`attempt ${attemptId} has no recorded intake decision; a `
			+ `destroyed runtime proves absence and decides nothing about the `
			+ `material`);
	}
	if (attempt.execution_runtime !== "destroyed") {
		return { cleanup: attempt.cleanup,
		         why: `execution is ${attempt.execution_runtime}; cleanup is `
		              + `complete when the runtime is observed destroyed` };
	}
	observe(store, { attemptId, axis: "cleanup", value: "complete" });
	return { cleanup: "complete" };
}
