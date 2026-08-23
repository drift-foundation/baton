// The read side.
//
// A projection is what an operator, a Worker Manager or a reviewer reads
// BEFORE acting, and §7 is emphatic that reading is not deciding: every
// value here is advisory the moment it is returned, and the atomic
// compare-and-swap in the write transaction is the arbiter.
//
// Two things are spelled out rather than left to be inferred, because
// inferring them is how the contract gets misread:
//
//   - `assignment` is the FULL four-part identity or null. It is never a
//     bare participant, so a caller cannot accidentally compare three
//     quarters of an identity and think it compared one.
//   - `ready` is false whenever a gate holds the Work, and the gate is
//     displayed beside it. §10.7 keeps offer, runtime, output, proposal,
//     cancellation, quiescence, intake and cleanup OFF the phase axis;
//     they become at most this one displayed gate.

import { assignmentRef, parseGate } from "./identity.mjs";

export function projectWork(store, authorityUuid, work) {
	const assignment = work.handler === null ? null : assignmentRef({
		authorityUuid, workId: work.work_id,
		participant: work.handler, generation: work.live_generation,
	});
	const fenced = store.all(
		"SELECT generation, cause, reason FROM fenced_generation WHERE work_id = ? "
		+ "ORDER BY generation", work.work_id);
	return {
		authorityUuid,
		workId: work.work_id,
		route: work.route,
		status: work.status,
		phase: work.phase,
		outcome: work.outcome,
		rationale: work.rationale,
		handler: work.handler,
		contract: work.contract,
		generationCounter: work.generation_counter,
		liveGeneration: work.live_generation,
		assignment,
		gate: work.gate === null ? null : { token: work.gate, ...parseGate(work.gate) },
		fencedGenerations: fenced.map((row) => ({
			generation: row.generation, cause: row.cause, reason: row.reason,
		})),
		// Readiness is a derived READ. It says the Work could be claimed at
		// the instant it was projected and nothing more; the claim
		// transaction rechecks every one of these.
		ready: work.status === "open" && work.phase === "queued"
			&& work.handler === null && work.gate === null,
	};
}
