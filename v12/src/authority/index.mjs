// The disposable v12 assignment authority's PUBLIC boundary.
//
// The next M2 slice — the durable Worker Manager core — consumes this
// module and nothing deeper. Reaching past it into `store.mjs` would let
// a manager write authority state directly, which is precisely the
// "manager-local or sidecar identity" the assignment boundary calls
// non-conforming: the authority, not the manager, allocates generations
// and decides claim, retirement, cancellation, gate and close outcomes.
//
// TWO FACES, AND W2929 HOLDS THE SECOND ONE.
//
//   `V12Authority` is the TRUSTED BOOTSTRAP. It certifies contracts,
//   permits contract transitions, grants capabilities, sets policy,
//   creates Work — and vends sessions. A deployment constructs exactly
//   one, at start-up, and does not hand it to a worker or a manager.
//
//   `V12Session` is the RUNTIME BOUNDARY. It is minted by the authority,
//   bound to one participant, and is what a Worker Manager holds. Every
//   transition lives here; none of the configuration does. The actor on
//   a receipt and the claimant on a claim come from the binding, so a
//   holder can neither grant itself authority nor act as anybody else.
//
// Re-review 2026-08-22 [P1] is why: with one object, a consumer of this
// module granted itself `close`, closed a live Work, and replaced the
// canonical target with zero proposals and zero receipts.

export { V12Authority, V12Session } from "./authority.mjs";
export { Refusal } from "./errors.mjs";
export {
	GATE_CONTRACT_RUNTIME, GATE_PLAN_REVISION, GATE_QUIESCENCE,
	V11, V12, assignmentRef, gateToken, isV12Contract, normalizeAssignment,
	parseGate, sameAssignment, signatureOf, snapshot,
} from "./identity.mjs";
export { projectWork } from "./projection.mjs";
export { CAPABILITIES } from "./authority.mjs";
