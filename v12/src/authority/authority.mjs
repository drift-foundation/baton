// The disposable v12 assignment authority.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-assignment-state-machine/SPEC.md` version `1-ruled` is the
// contract; this is the executable implementation of the half of it the
// AUTHORITY owns. The Worker Manager control store — offers, runtime
// attempts, quarantined output, runtime observations — is a separate
// deliverable and deliberately absent here (§3): an authority that also
// stored a runtime observation would be answering a question it is not
// authoritative for.
//
// It is SELF-CONTAINED. Nothing in this subtree imports `src/baton_work/`,
// opens a v11 `work.sqlite3`, or shells out to a v11 executable. V11
// concepts are reused as concepts; no v11 code is.
//
// FOUR PROPERTIES CARRY THE WHOLE CONTRACT, and every method below is
// arranged around them:
//
//   1. IDENTITY IS FOUR-PART. `(authority UUID, full Work ID,
//      participant, generation)`. Participant equality settles nothing —
//      the same participant may release generation 7 and immediately
//      claim generation 8 — so every assignment-owned act compare-and-
//      swaps the whole thing (§8, §10.4).
//   2. ENDING AN ASSIGNMENT IS ONE HELPER. `#endAssignment` is called by
//      every Handler-clear path. V11's six separate clear paths are why:
//      a fence added to `release` alone leaves five doors open (§2, §7).
//   3. FENCE AND END COMMIT TOGETHER. Cancellation fences the exact
//      generation AND ends the assignment in ONE transaction, so there is
//      no observable instant in which publication has died but the board
//      still shows somebody executing (§5, §10.5).
//   4. AN OPERATION IDENTITY IS DURABLY IN ONE OF FOUR STATES.
//      UNSUBMITTED, COMMITTED, REFUSED (only when the refusal wrote
//      something), RETIRED. Retirement closes the identity to every later
//      submitter and BINDS the disposition it caused, so a manager that
//      crashes between the authority act and its own row cannot let the
//      next entry path relabel the outcome (§4, §10.17).

import { randomUUID } from "node:crypto";

import { Refusal } from "./errors.mjs";
import {
	GATE_CONTRACT_RUNTIME, GATE_PLAN_REVISION, GATE_QUIESCENCE,
	V11, assignmentKey, assignmentRef, gateToken, isV12Contract,
	normalizeAssignment, parseGate, sameAssignment, signatureOf, snapshot,
} from "./identity.mjs";
import { Store } from "./store.mjs";
import { projectWork } from "./projection.mjs";

const CLOSED_PHASES = new Set(["queued", "active", "block", "parked"]);
// The phases an UNCLAIMED Work can be in. `active` is absent on purpose: it
// means exactly "a Handler holds it", and only `claim` reaches it.
const UNCLAIMED_PHASES = new Set(["queued", "block", "parked"]);
const UNCLAIMABLE_PHASES = new Set(["block", "parked"]);
const GATE_KINDS = new Set([GATE_QUIESCENCE, GATE_CONTRACT_RUNTIME,
                            GATE_PLAN_REVISION]);
// What `end` may call itself. Every other ending has its own transition,
// because every other ending derives a different scheduler outcome.
const RELEASE_DISPOSITIONS = new Set(["release", "recovered"]);
// The configured capabilities §7's actor column names. Exported so a
// deployment configures them from one list rather than from string
// literals scattered across its setup.
export const CAPABILITIES = Object.freeze(
	["verify", "review", "approve", "integrate", "close"]);
const CAPABILITY_SET = new Set(CAPABILITIES);

// Strict operands, for the transitions whose outcome is DERIVED. A caller
// that supplies one and has it ignored believes it chose something.
function assertNoExtraOperands(what, rest, explanation) {
	const extra = Object.keys(rest);
	if (extra.length) {
		throw new Refusal(
			`${what} does not take ${extra.join(", ")}; ${explanation}`);
	}
}
const INTAKE_OUTCOMES = new Set(["satisfying", "non-satisfying", "rejected", "cancelled"]);

// The implementation, and NOT a public object. Nothing outside this module
// ever holds a `Core`: the two exported faces below each expose the subset
// their holder is entitled to, and `Core` is what makes them one
// implementation rather than two that can drift.
class Core {
	#store;
	#uuid;
	// The one fault-injection seam in this module, and it is here because
	// §8 turns on the difference between "it did not commit" and "I could
	// not ask". A store or transport fault has to be reachable in a test
	// or the rule that an unanswerable lookup settles NOTHING is
	// unprovable. It affects only `operationResult`.
	#lookupAvailable = true;

	constructor(store) {
		this.#store = store;
		this.#uuid = store.authorityUuid;
	}

	get authorityUuid() { return this.#uuid; }

	// There is deliberately NO public accessor for the store, the database,
	// or any SQL runner.
	//
	// Review 2026-08-22 [P1]: a `store` getter used to be here, and through
	// it a consumer of the advertised boundary set `generation_counter` to
	// 41 and then claimed normally, receiving generation 42. The consumer
	// had chosen the supposedly authority-minted generation, and could
	// equally have rewritten Handler, fences, operations, gates, proposals
	// and receipts. "The authority, not the manager, allocates generations"
	// is not a property a comment can hold; it is a property of there being
	// no other door.

	// -- deployment policy -------------------------------------------------

	certifyContract(contract, profile = "reference") {
		this.#store.run(
			"INSERT INTO certified_contract (contract, profile, certified_at) "
			+ "VALUES (?, ?, ?) ON CONFLICT (contract) DO UPDATE SET profile = excluded.profile",
			contract, profile, new Date().toISOString());
	}

	withdrawCertification(contract) {
		this.#store.run("DELETE FROM certified_contract WHERE contract = ?", contract);
	}

	isCertified(contract) {
		return this.#store.get(
			"SELECT 1 AS ok FROM certified_contract WHERE contract = ?", contract) !== undefined;
	}

	permitContractTransition(from, to) {
		this.#store.run(
			"INSERT INTO contract_transition (from_contract, to_contract) VALUES (?, ?) "
			+ "ON CONFLICT DO NOTHING", from, to);
	}

	permitsContractTransition(from, to) {
		return this.#store.get(
			"SELECT 1 AS ok FROM contract_transition WHERE from_contract = ? "
			+ "AND to_contract = ?", from, to) !== undefined;
	}

	setPolicy(key, value) {
		this.#store.run(
			"INSERT INTO policy (key, value) VALUES (?, ?) "
			+ "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
			key, JSON.stringify(value));
	}

	policy(key, fallback = null) {
		const row = this.#store.get("SELECT value FROM policy WHERE key = ?", key);
		return row === undefined ? fallback : JSON.parse(row.value);
	}

	canonicalTarget() { return this.policy("canonical_target", "base-1"); }

	// The seam described on `#lookupAvailable`.
	setLookupAvailable(available) { this.#lookupAvailable = Boolean(available); }

	// -- configured capabilities -------------------------------------------
	//
	// §7 names a distinct actor for the receipt transitions — verifier,
	// `rview`, `approv`, trusted integrator — and an authorized actor
	// holding the close capability. Review 2026-08-22 [P1]: none of those
	// transitions took an actor at all, so one consumer could carry a
	// candidate from publication to integration and close the Work by
	// itself.
	//
	// A deployment MAY grant one participant several of these; §10.12 says
	// the receipts stay distinct even then, because each records who wrote
	// it. What a deployment cannot do is leave the question unasked.

	grantCapability(participant, capability) {
		if (!CAPABILITY_SET.has(capability)) {
			throw new Refusal(
				`unknown capability ${capability}; this authority knows `
				+ `${CAPABILITIES.join(", ")}`);
		}
		this.#store.run(
			"INSERT INTO capability (participant, capability, granted_at) "
			+ "VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
			participant, capability, new Date().toISOString());
	}

	revokeCapability(participant, capability) {
		this.#store.run(
			"DELETE FROM capability WHERE participant = ? AND capability = ?",
			participant, capability);
	}

	holdsCapability(participant, capability) {
		return this.#store.get(
			"SELECT 1 AS ok FROM capability WHERE participant = ? AND capability = ?",
			participant, capability) !== undefined;
	}

	capabilitiesOf(participant) {
		return this.#store.all(
			"SELECT capability FROM capability WHERE participant = ? ORDER BY capability",
			participant).map((row) => row.capability);
	}

	// An ordinary refusal: it writes nothing, so an actor granted the
	// capability afterwards may simply retry with a NEW operation id.
	#requireCapability(actor, capability, what) {
		if (typeof actor !== "string" || actor === "") {
			throw new Refusal(
				`a ${what} is separately attributable and needs the participant `
				+ `writing it`);
		}
		if (!this.holdsCapability(actor, capability)) {
			throw new Refusal(
				`${actor} does not hold the ${capability} capability; a ${what} is `
				+ `written by the configured actor, not by whoever holds the object`);
		}
	}

	// -- Work and route ----------------------------------------------------

	// Creation mints an UNCLAIMED Work, so the phases it may take are the
	// unclaimed ones.
	//
	// Review 2026-08-22 [P1]: this accepted `phase="active"` and committed a
	// Handler-null/active row, which `assertInvariants` then reported after
	// the corruption was already durable. Invariants are a backstop; the
	// transition is where an impossible state is refused. `active` means
	// exactly "a Handler holds it", and only `claim` reaches it.
	createWork({ workId, route, contract = V11, phase = "queued", gate = null,
	             ...rest }) {
		assertNoExtraOperands("createWork", rest,
			"a Work is created with an id, a route, a contract and an unclaimed "
			+ "scheduler state");
		if (!UNCLAIMED_PHASES.has(phase)) {
			throw new Refusal(
				`a Work is created unclaimed, so its phase is one of `
				+ `${[...UNCLAIMED_PHASES].join(", ")}; ${phase} is not reachable `
				+ `without a Handler`);
		}
		this.#assertPhaseGate(phase, gate);
		this.#store.run(
			"INSERT INTO work (work_id, route, status, phase, gate, contract, "
			+ "created_at) VALUES (?, ?, 'open', ?, ?, ?, ?)",
			workId, route, phase, gate, contract, new Date().toISOString());
		return this.projectWork(workId);
	}

	// The one place the scheduler cross-product is checked, called by every
	// transition that writes a phase or a gate.
	//
	// A gate is a REASON the Work cannot run, so a gate without `block` and
	// a `block` without a gate are both states nobody can act on or explain.
	// The token must also be a typed one with a non-empty detail: an
	// unparseable gate can never be satisfied, because `satisfyGate` has no
	// kind to check evidence against.
	#assertPhaseGate(phase, gate) {
		if (phase !== null && !CLOSED_PHASES.has(phase)) {
			throw new Refusal(`unknown phase ${phase}`);
		}
		if (gate === null) {
			if (phase === "block") {
				throw new Refusal("a blocked Work must name the one gate holding it");
			}
			return;
		}
		if (phase !== "block") {
			throw new Refusal(
				`a gate is what holds a Work in block; ${gate} cannot be installed `
				+ `with phase ${phase}`);
		}
		const parsed = parseGate(gate);
		if (parsed === null || !GATE_KINDS.has(parsed.kind) || parsed.detail === "") {
			throw new Refusal(
				`${gate} is not a typed gate token; a gate names one of `
				+ `${[...GATE_KINDS].join(", ")} and a non-empty detail`);
		}
	}

	addRouteHandler(route, participant) {
		this.#store.run(
			"INSERT INTO route_handler (route, participant) VALUES (?, ?) "
			+ "ON CONFLICT DO NOTHING", route, participant);
	}

	#work(workId) {
		const row = this.#store.get("SELECT * FROM work WHERE work_id = ?", workId);
		if (row === undefined) throw new Refusal(`no such Work ${workId}`);
		return row;
	}

	projectWork(workId) {
		return projectWork(this.#store, this.#uuid, this.#work(workId));
	}

	// The Work's live assignment, or null. This is a PROJECTION of durable
	// columns, never a cache: `handler` and `live_generation` move in one
	// transaction, so they cannot disagree here.
	assignmentOf(workId) {
		const work = this.#work(workId);
		if (work.handler === null) return null;
		return assignmentRef({
			authorityUuid: this.#uuid, workId: work.work_id,
			participant: work.handler, generation: work.live_generation,
		});
	}

	fencedGenerations(workId) {
		return this.#store.all(
			"SELECT generation FROM fenced_generation WHERE work_id = ? "
			+ "ORDER BY generation", workId).map((row) => row.generation);
	}

	#isFenced(workId, generation) {
		if (generation === null || generation === undefined) return false;
		return this.#store.get(
			"SELECT 1 AS ok FROM fenced_generation WHERE work_id = ? AND generation = ?",
			workId, generation) !== undefined;
	}

	// The compare-and-swap every assignment-owned act performs.
	//
	// The FENCED case gets its own refusal on purpose. "Stale assignment"
	// and "your generation was ended and fenced" are different facts, and
	// a late worker deserves to be told which one applies to it — the
	// second means the assignment is gone for good, not that it lost a
	// race it might win on retry.
	#expect(expected, { what = "assignment" } = {}) {
		if (expected === null || expected === undefined) {
			throw new Refusal(
				`this act is assignment-owned and needs an exact ${what} identity`);
		}
		assignmentKey(expected, { what });
		if (expected.authorityUuid !== this.#uuid) {
			throw new Refusal(
				`assignment names authority ${expected.authorityUuid}, not ${this.#uuid}`);
		}
		const current = this.assignmentOf(expected.workId);
		if (sameAssignment(current, expected)) return this.#work(expected.workId);
		if (this.#isFenced(expected.workId, expected.generation)) {
			throw new Refusal("assignment generation was fenced and ended");
		}
		throw new Refusal("stale assignment");
	}

	// -- claim capacity ----------------------------------------------------

	slotHolder(participant) {
		const row = this.#store.get(
			"SELECT work_id FROM claim_slot WHERE participant = ?", participant);
		return row === undefined ? null : row.work_id;
	}

	#takeSlot(participant, workId, generation) {
		const held = this.slotHolder(participant);
		if (held !== null && held !== workId) {
			throw new Refusal(
				`${participant} already holds ${held}; a participant holds ONE `
				+ `active claim at a time`);
		}
		this.#store.run(
			"INSERT INTO claim_slot (participant, work_id, generation, taken_at) "
			+ "VALUES (?, ?, ?, ?) ON CONFLICT (participant) DO UPDATE SET "
			+ "work_id = excluded.work_id, generation = excluded.generation",
			participant, workId, generation, new Date().toISOString());
	}

	#releaseSlot(participant, workId) {
		this.#store.run(
			"DELETE FROM claim_slot WHERE participant = ? AND work_id = ?",
			participant, workId);
	}

	// -- the operation journal --------------------------------------------

	// §8's read-only operation-result lookup, or null when nothing has
	// committed. It RAISES when the authority cannot answer, because "I
	// could not ask" must never be read as "it did not commit".
	operationResult(operationId) {
		if (!this.#lookupAvailable) {
			throw new Refusal("the operation-result lookup is unavailable");
		}
		const row = this.#store.operationRow(operationId);
		if (row === null || row.state !== "committed") return null;
		return JSON.parse(row.result);
	}

	operationRecord(operationId) { return this.#store.operationRecord(operationId); }

	// The operands a fixed claim operation commits under. The Work is part
	// of it: this authority holds many Works, and an operation id that
	// meant "claim by this participant" without saying WHICH Work would
	// collide across them.
	static claimSignature(workId, participant) {
		return signatureOf("claim", { workId, participant });
	}

	dispose() { this.#store.close(); }

	// Make one fixed operation durably terminal, in ONE authority act.
	//
	// A read that says "not committed" proves only its own instant: a
	// submitter may already have passed its preconditions and commit right
	// after the read. So this is not lookup-then-write. It is one
	// transaction that either finds the committed result or RETIRES the
	// identity so nothing can ever commit under it again.
	//
	// `signature` is the FIXED operation the caller believes it is
	// settling. An id alone proves only that SOMETHING committed under it,
	// so a record with different operands is a COLLISION: it fails closed,
	// adopts nothing, and overwrites nothing (§10.16).
	//
	// `mayRetire` is the caller's settlement authority, and it defaults to
	// FALSE. Retirement kills a live authorization, so a caller with no
	// positive evidence that the operation is over — a timeout before its
	// deadline — may only observe (§10.15).
	//
	// Review 2026-08-22 [P1]: it used to default to true, so omitting the
	// operand retired an unsubmitted claim on the spot. The safe public
	// default is the opposite: settlement authority is something a caller
	// asserts, never something it inherits by saying nothing.
	//
	// `disposition` is the terminal outcome this retirement CAUSES, and it
	// is bound with it. The authority record and a manager's control row
	// are separate durability boundaries; binding the disposition is what
	// stops the next caller, arriving on whatever entry path it happens to
	// be on, from relabelling a settlement timeout as a refused claim
	// (§10.17).
	settleOperation({ operationId, signature, reason, disposition, mayRetire = false }) {
		// Raises when the authority cannot answer at all.
		this.operationResult(operationId);
		return this.#store.transact(() => {
			// Re-read INSIDE the settlement. Anything that committed while
			// the lookup was in flight is found here, and after this act the
			// identity is closed to every later and stale submitter alike.
			const prior = this.#store.operationRow(operationId);
			if (prior !== null) {
				if (prior.state === "retired") {
					return { kind: "retired", record: JSON.parse(prior.detail) };
				}
				if (prior.signature !== signature) {
					throw new Refusal("operation id was reused for different operands");
				}
				if (prior.state === "committed") {
					return { kind: "committed", result: JSON.parse(prior.result) };
				}
				return { kind: "refused", detail: prior.detail };
			}
			if (!mayRetire) return { kind: "live", record: null };
			const record = { reason, disposition };
			this.#store.recordRetirement(operationId, signature, record);
			return { kind: "retired", record };
		});
	}

	// -- claim -------------------------------------------------------------

	claim({ workId, participant, operationId }) {
		return this.#store.replay(
			operationId, V12Authority.claimSignature(workId, participant),
			() => {
				const work = this.#work(workId);
				if (work.status !== "open") throw new Refusal("Work is not claimable");
				if (UNCLAIMABLE_PHASES.has(work.phase)) {
					throw new Refusal(
						work.gate === null
							? `Work is ${work.phase}; blocked and parked work cannot be claimed`
							: `Work is blocked by ${work.gate}; blocked work cannot be claimed`);
				}
				if (work.handler !== null) throw new Refusal("Work is already claimed");
				const eligible = this.#store.get(
					"SELECT 1 AS ok FROM route_handler WHERE route = ? AND participant = ?",
					work.route, participant);
				if (eligible === undefined) {
					throw new Refusal(
						`route ${work.route} does not resolve to ${participant}`);
				}
				// Capacity is checked HERE, inside the write transaction, as
				// well as at offer issue. Checking it only at issue would make
				// it advisory (§10.2).
				let generation = null;
				if (isV12Contract(work.contract)) {
					generation = work.generation_counter + 1;
				}
				this.#takeSlot(participant, workId, generation);
				this.#store.run(
					"UPDATE work SET handler = ?, phase = 'active', "
					+ "generation_counter = ?, live_generation = ? WHERE work_id = ?",
					participant,
					generation === null ? work.generation_counter : generation,
					generation, workId);
				return this.assignmentOf(workId);
			});
	}

	// -- the ONE assignment-ending helper ----------------------------------
	//
	// Every Handler-clear path calls this and nothing else clears Handler.
	// The event it appends names the ended assignment, the cause, whether
	// the generation was fenced, and the gate the transition derived, so
	// the journal answers "who lost the Work and why" without inference.
	#endAssignment(expected, { phase, gate = null, cause, fence = false, reason = null }) {
		// Checked BEFORE the compare-and-swap, so an impossible outcome
		// refuses without touching state or the journal.
		this.#assertPhaseGate(phase, gate);
		const work = this.#expect(expected);
		if (fence && expected.generation !== null && expected.generation !== undefined) {
			this.#store.run(
				"INSERT INTO fenced_generation (work_id, generation, cause, reason, "
				+ "fenced_at) VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
				work.work_id, expected.generation, cause, reason,
				new Date().toISOString());
		}
		this.#releaseSlot(work.handler, work.work_id);
		this.#store.run(
			"UPDATE work SET handler = NULL, live_generation = NULL, phase = ?, "
			+ "gate = ? WHERE work_id = ?", phase, gate, work.work_id);
		this.#store.run(
			"INSERT INTO assignment_event (work_id, participant, generation, cause, "
			+ "fenced, reason, gate, phase, at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
			work.work_id, expected.participant, expected.generation, cause,
			fence ? 1 : 0, reason, gate, phase, new Date().toISOString());
		return { cause, assignment: expected, phase, gate, fenced: fence };
	}

	assignmentEvents(workId) {
		return this.#store.all(
			"SELECT * FROM assignment_event WHERE work_id = ? ORDER BY seq", workId);
	}

	// -- assignment-ending transitions -------------------------------------

	// Release: the assignment ends and the Work returns to the queue.
	//
	// Review 2026-08-22 [P1]: this used to take caller-supplied `phase` and
	// `gate`, so `end({..., phase: "active"})` committed a Handler-null
	// active row through the public boundary. §7 gives every transition a
	// DERIVED scheduler outcome; a release derives `queued` and no gate, and
	// a caller that wants a gate uses the transition that installs one.
	end({ expect, operationId, disposition = "release", reason = null, ...rest }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		// Strict operands. Silently ignoring `phase` would be safe now, but a
		// caller that passed it would believe it had chosen the outcome — and
		// that belief is exactly what the corrected transition removes.
		assertNoExtraOperands("end", rest,
			"a release derives its own phase and gate; use cancel, rejectPlan, "
			+ "installGate, pass or close for the outcomes that differ");
		if (!RELEASE_DISPOSITIONS.has(disposition)) {
			throw new Refusal(
				`${disposition} is not a release disposition; use the transition `
				+ `that owns it — cancel, rejectPlan, installGate, pass or close`);
		}
		return this.#store.replay(
			operationId, signatureOf("end", { expect, disposition, reason }),
			() => this.#endAssignment(expect,
				{ phase: "queued", gate: null, cause: disposition, fence: false, reason }));
	}

	// A pass moves the Route and ends the assignment in the same act. The
	// route move is v11's; the centralized end is what v11 does not have.
	pass({ expect, toRoute, operationId, comment }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId, signatureOf("pass", { expect, toRoute, comment }),
			() => {
				const work = this.#expect(expect);
				this.#store.run("UPDATE work SET route = ? WHERE work_id = ?",
					toRoute, work.work_id);
				return {
					...this.#endAssignment(expect,
						{ phase: "queued", cause: "pass", fence: false, reason: comment }),
					route: toRoute,
				};
			});
	}

	// Cancellation: fence the exact generation AND end the assignment in
	// ONE transaction (ruling 1). The participant's one global claim slot
	// is freed immediately; only the REPLACEMENT waits, behind the typed
	// gate this installs.
	cancel({ expect, operationId, reason }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId, signatureOf("cancel", { expect, reason }),
			() => {
				// Under `v11` there is no generation, so "fence the exact
				// generation AND end the assignment" would fence nothing and
				// install a `runtime-quiescence:null` gate naming no generation.
				// Half a guarantee spelled like a whole one is worse than a
				// refusal: advance the contract first.
				if (expect.generation === null || expect.generation === undefined) {
					throw new Refusal(
						"cancellation fences an exact generation and this assignment "
						+ "has none; only a v12 assignment contract can be cancelled");
				}
				return this.#endAssignment(expect, {
					phase: "block",
					gate: gateToken(GATE_QUIESCENCE, expect.generation),
					cause: "cancelled", fence: true, reason,
				});
			});
	}

	// A plan rejection cannot reoffer the unchanged plan, because the gate
	// is installed atomically with the assignment end (§11).
	rejectPlan({ expect, operationId, planDigest, reason }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId, signatureOf("reject-plan", { expect, planDigest, reason }),
			() => this.#endAssignment(expect, {
				phase: "block",
				gate: gateToken(GATE_PLAN_REVISION, planDigest),
				cause: "plan-rejected", fence: false, reason,
			}));
	}

	// Gate arrival and the explicit unclaimed phase change. If a Handler
	// exists the caller must name its exact assignment: a scheduler event
	// that silently discarded a live assignment is precisely the
	// uncentralized ending this contract exists to prevent.
	installGate({ workId, gate, reason, operationId, expect = undefined }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId, signatureOf("install-gate", { workId, gate, reason, expect }),
			() => {
				this.#assertPhaseGate("block", gate);
				const work = this.#work(workId);
				if (work.handler === null) {
					this.#store.run(
						"UPDATE work SET phase = 'block', gate = ? WHERE work_id = ?",
						gate, workId);
					return { gate, phase: "block", assignment: null };
				}
				if (expect === undefined) {
					throw new Refusal(
						"this Work has a live assignment; a gate arrival that ends it "
						+ "must supply the exact assignment identity");
				}
				return this.#endAssignment(expect, {
					phase: "block", gate, cause: "gate-arrival", fence: false, reason,
				});
			});
	}

	// -- gates -------------------------------------------------------------

	satisfyGate({ workId, gate, evidence, operationId }) {
		// The evidence is journalled AND checked, so it is snapshotted for
		// the same reason an assignment is.
		evidence = snapshot(evidence);
		return this.#store.replay(
			operationId, signatureOf("satisfy-gate", { workId, gate, evidence }),
			() => {
				const work = this.#work(workId);
				if (work.gate === null || work.gate !== gate) {
					throw new Refusal("that gate is not the one holding this Work");
				}
				const parsed = parseGate(gate);
				const kind = evidence?.kind;
				if (parsed?.kind === GATE_QUIESCENCE) {
					// §10.8: an unreachable runtime is NOT a dead one. Only
					// positive absence, or an explicitly pinned certified-isolation
					// clause, releases the replacement.
					if (kind === "runtime-absent") {
						if (!evidence.runtime) {
							throw new Refusal(
								"positive absence must name the exact runtime it observed");
						}
					} else if (kind === "certified-isolation-policy") {
						if (!this.policy("isolation_certified", false)) {
							throw new Refusal("replacement is not permitted");
						}
						if (!evidence.policy) throw new Refusal("replacement is not permitted");
					} else {
						throw new Refusal("replacement is not permitted");
					}
				} else if (parsed?.kind === GATE_CONTRACT_RUNTIME) {
					if (kind !== "certified-profile" || !this.isCertified(work.contract)) {
						throw new Refusal(
							"no certified runtime profile executes this contract");
					}
				} else if (parsed?.kind === GATE_PLAN_REVISION) {
					if (kind !== "revised-plan" || !evidence.plan_digest) {
						throw new Refusal("a plan-revision gate needs a revised plan digest");
					}
					if (evidence.plan_digest === parsed.detail) {
						throw new Refusal(
							"the plan digest is unchanged; a plan-revision gate cannot be "
							+ "satisfied by reoffering the rejected plan");
					}
				} else {
					throw new Refusal("unknown gate kind");
				}
				this.#store.run(
					"INSERT INTO gate_evidence (work_id, gate, evidence, at) "
					+ "VALUES (?, ?, ?, ?)",
					workId, gate, JSON.stringify(evidence), new Date().toISOString());
				this.#store.run(
					"UPDATE work SET gate = NULL, phase = 'queued' WHERE work_id = ?",
					workId);
				return { gate, kind, phase: "queued" };
			});
	}

	gateEvidence(workId) {
		return this.#store.all(
			"SELECT * FROM gate_evidence WHERE work_id = ? ORDER BY seq", workId)
			.map((row) => ({ ...row, evidence: JSON.parse(row.evidence) }));
	}

	// -- contract progression ----------------------------------------------

	advanceContract({ expect, expectContract, targetContract, rationale, operationId }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId,
			signatureOf("advance-contract",
				{ expect, expectContract, targetContract, rationale }),
			() => {
				const work = this.#expect(expect);
				if (work.contract !== expectContract) {
					throw new Refusal("contract compare-and-swap is stale");
				}
				if (!this.permitsContractTransition(expectContract, targetContract)) {
					throw new Refusal("contract transition is not permitted by policy");
				}
				// A Work may intentionally advance to a contract whose runtime is
				// not deployed yet. It stays the same Work and waits visibly on a
				// typed gate rather than being recreated or misclaimed (§11).
				const certified = this.isCertified(targetContract);
				const gate = certified
					? null : gateToken(GATE_CONTRACT_RUNTIME, targetContract);
				const phase = certified ? "queued" : "block";
				this.#store.run("UPDATE work SET contract = ? WHERE work_id = ?",
					targetContract, work.work_id);
				this.#store.run(
					"INSERT INTO contract_event (work_id, from_contract, to_contract, "
					+ "participant, generation, rationale, at) VALUES (?, ?, ?, ?, ?, ?, ?)",
					work.work_id, expectContract, targetContract, expect.participant,
					expect.generation, rationale, new Date().toISOString());
				this.#endAssignment(expect, {
					phase, gate, cause: "contract-advanced", fence: false,
					reason: rationale,
				});
				return { contract: targetContract, phase, gate };
			});
	}

	contractEvents(workId) {
		return this.#store.all(
			"SELECT * FROM contract_event WHERE work_id = ? ORDER BY seq", workId);
	}

	// -- canonical activity ------------------------------------------------

	activity({ expect, key }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.transact(() => {
			const work = this.#expect(expect);
			this.#store.run(
				"INSERT INTO activity (work_id, participant, generation, action_key, at) "
				+ "VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING",
				work.work_id, expect.participant, expect.generation, key,
				new Date().toISOString());
			return this.#store.get(
				"SELECT * FROM activity WHERE work_id = ? AND participant = ? "
				+ "AND generation IS ? AND action_key = ?",
				work.work_id, expect.participant, expect.generation, key);
		});
	}

	activities(workId) {
		return this.#store.all(
			"SELECT * FROM activity WHERE work_id = ? ORDER BY seq", workId);
	}

	// -- proposal and the four workflow receipts ---------------------------

	// §10.11: the receipt binds the exact assignment AND the input, policy,
	// output, candidate-tree and target digests; §4 adds the frozen result
	// identity and its content digest.
	//
	// Review 2026-08-22 [P1]: this took one undifferentiated `digest`, so a
	// published candidate could not say what it had been built FROM — the
	// input it consumed, the policy it ran under, or the frozen output it
	// came from. Every one of them is required, and every one rides the
	// operation signature: later bytes are a NEW proposal, and an id reused
	// for different bytes refuses rather than replaying.
	publish({ expect, proposalId, resultId, resultDigest, candidateDigest,
	          inputDigest, policyDigest, target = null, operationId }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		const wanted = target ?? this.canonicalTarget();
		const digests = { resultId, resultDigest, candidateDigest, inputDigest,
		                  policyDigest };
		return this.#store.replay(
			operationId,
			signatureOf("publish", { expect, proposalId, ...digests, target }),
			() => {
				for (const [name, value] of Object.entries(digests)) {
					if (typeof value !== "string" || value === "") {
						throw new Refusal(
							`a proposal receipt binds the exact assignment and the result, `
							+ `candidate, input and policy digests; ${name} is missing`);
					}
				}
				const work = this.#expect(expect);
				if (!isV12Contract(work.contract)) {
					throw new Refusal("publication requires a v12 assignment contract");
				}
				const prior = this.#store.get(
					"SELECT * FROM proposal WHERE proposal_id = ?", proposalId);
				if (prior !== undefined) {
					const same = prior.work_id === work.work_id
						&& prior.participant === expect.participant
						&& prior.generation === expect.generation
						&& prior.result_id === resultId
						&& prior.result_digest === resultDigest
						&& prior.candidate_digest === candidateDigest
						&& prior.input_digest === inputDigest
						&& prior.policy_digest === policyDigest
						&& prior.target === wanted;
					if (!same) {
						throw new Refusal("proposal identity was reused for different bytes");
					}
					return { proposalId, ...digests, target: wanted };
				}
				this.#store.run(
					"INSERT INTO proposal (proposal_id, work_id, participant, generation, "
					+ "result_id, result_digest, candidate_digest, input_digest, "
					+ "policy_digest, target, published_at) "
					+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
					proposalId, work.work_id, expect.participant, expect.generation,
					resultId, resultDigest, candidateDigest, inputDigest, policyDigest,
					wanted, new Date().toISOString());
				return { proposalId, ...digests, target: wanted };
			});
	}

	proposal(proposalId) {
		const row = this.#store.get(
			"SELECT * FROM proposal WHERE proposal_id = ?", proposalId);
		if (row === undefined) throw new Refusal("no such proposal");
		return row;
	}

	receipts(proposalId) {
		return this.#store.all(
			"SELECT * FROM receipt WHERE proposal_id = ? ORDER BY recorded_at, kind",
			proposalId);
	}

	receipt(proposalId, kind) {
		return this.#store.get(
			"SELECT * FROM receipt WHERE proposal_id = ? AND kind = ?",
			proposalId, kind) ?? null;
	}

	// The four receipts are separately attributable and IMMUTABLE (§10.12).
	//
	// Review 2026-08-22 [P1]: they used to be disposition STRINGS on the
	// proposal with no actor and no authorization, so one consumer could
	// publish a candidate, self-verify, self-review, self-approve, integrate
	// it into the canonical target and close the Work. Each receipt now
	// carries its own identity, the actor who wrote it, and the candidate
	// digest and target revision that actor was looking at — and the actor
	// must hold the configured capability for that step.
	//
	// A deployment MAY grant one participant several capabilities; §10.12
	// says the receipts stay distinct even then. What it cannot do is leave
	// the question unasked.
	#writeReceipt({ kind, capability, valid, proposalId, receiptId, actor,
	                disposition, operationId, precondition, policyGeneration = null }) {
		return this.#store.replay(
			operationId,
			// EVERY durable operand, including the policy generation an
			// approval binds (re-review 2026-08-22 [P1]).
			signatureOf(kind, { proposalId, receiptId, actor, disposition,
			                    policyGeneration }),
			() => {
				if (typeof receiptId !== "string" || receiptId === "") {
					throw new Refusal(`a ${kind} receipt needs its own identity`);
				}
				this.#requireCapability(actor, capability, kind);
				if (!valid.has(disposition)) throw new Refusal(`invalid ${kind} disposition`);
				const proposal = this.proposal(proposalId);
				if (this.receipt(proposalId, kind) !== null) {
					throw new Refusal(`${kind} receipt is immutable`);
				}
				if (precondition) precondition(proposal);
				this.#store.run(
					"INSERT INTO receipt (receipt_id, kind, proposal_id, actor, "
					+ "disposition, candidate_digest, target, policy_generation, "
					+ "recorded_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
					receiptId, kind, proposalId, actor, disposition,
					proposal.candidate_digest, proposal.target, policyGeneration,
					new Date().toISOString());
				return { kind, receiptId, proposalId, actor, disposition,
				         policyGeneration,
				         candidateDigest: proposal.candidate_digest,
				         target: proposal.target };
			});
	}

	#dispositionOf(proposalId, kind) {
		return this.receipt(proposalId, kind)?.disposition ?? null;
	}

	verify({ proposalId, verificationId, actor, observation, operationId }) {
		return this.#writeReceipt({
			kind: "verification", capability: "verify",
			valid: new Set(["passed", "failed", "unable"]),
			proposalId, receiptId: verificationId, actor, disposition: observation,
			operationId });
	}

	review({ proposalId, reviewId, actor, disposition, operationId }) {
		return this.#writeReceipt({
			kind: "review", capability: "review",
			valid: new Set(["accepted", "changes-requested", "rejected"]),
			proposalId, receiptId: reviewId, actor, disposition, operationId,
			precondition: () => {
				if (this.#dispositionOf(proposalId, "verification") !== "passed") {
					throw new Refusal("technical review requires passed verification");
				}
			} });
	}

	// The policy generation an approval was granted UNDER is a durable
	// operand of the receipt, so §10.13 puts it in the operation identity.
	//
	// Re-review 2026-08-22 [P1]: it was optional and outside the signature,
	// so committing operation `app` under generation 7 and resubmitting the
	// same id under 8 REPLAYED success instead of colliding — one identity
	// taking two different durable meanings — and omitting it entirely
	// committed NULL while the record claimed approval binds it.
	approve({ proposalId, approvalId, actor, disposition, operationId,
	          policyGeneration }) {
		if (!Number.isInteger(policyGeneration) || policyGeneration < 1) {
			throw new Refusal(
				"an approval binds the configured policy generation it was granted "
				+ "under; supply a positive integer");
		}
		return this.#writeReceipt({
			kind: "approval", capability: "approve",
			valid: new Set(["approved", "denied"]),
			proposalId, receiptId: approvalId, actor, disposition, operationId,
			policyGeneration,
			precondition: () => {
				if (this.#dispositionOf(proposalId, "review") !== "accepted") {
					throw new Refusal("approval requires accepted technical review");
				}
			} });
	}

	// Integration is the one transition whose REFUSAL can write something:
	// the stale-target attempt is journalled beside the proposal before it
	// refuses, so the retry replays that refusal instead of appending a
	// second attempt or taking a different outcome under one identity.
	//
	// Review 2026-08-22 [P1]: the durable flag used to be on the CALL, so
	// every integration refusal — including a pre-approval one that wrote
	// nothing — was recorded REFUSED and permanently closed. Only the
	// refusal that actually journalled its attempt is marked durable now.
	integrate({ proposalId, integrationId, actor, operationId }) {
		return this.#store.replay(
			operationId, signatureOf("integrate", { proposalId, integrationId, actor }),
			() => {
				if (typeof integrationId !== "string" || integrationId === "") {
					throw new Refusal("an integration receipt needs its own identity");
				}
				this.#requireCapability(actor, "integrate", "integration");
				const proposal = this.proposal(proposalId);
				if (this.receipt(proposalId, "integration") !== null) {
					throw new Refusal("integration receipt is immutable");
				}
				// Ordinary refusals: they write nothing and stay retryable.
				if (this.#dispositionOf(proposalId, "verification") !== "passed") {
					throw new Refusal("integration requires passed verification");
				}
				if (this.#dispositionOf(proposalId, "review") !== "accepted") {
					throw new Refusal("integration requires accepted technical review");
				}
				if (this.#dispositionOf(proposalId, "approval") !== "approved") {
					throw new Refusal("integration requires explicit approval");
				}
				const target = this.canonicalTarget();
				if (target !== proposal.target) {
					this.#store.run(
						"INSERT INTO integration_attempt (proposal_id, actor, reason, "
						+ "target, at) VALUES (?, ?, 'stale-target', ?, ?)",
						proposalId, actor, target, new Date().toISOString());
					// DURABLE: this one journalled its attempt, so the refusal is
					// itself a committed outcome of this operation identity.
					throw new Refusal("canonical target moved", { durable: true });
				}
				this.setPolicy("canonical_target", proposal.candidate_digest);
				this.#store.run(
					"INSERT INTO receipt (receipt_id, kind, proposal_id, actor, "
					+ "disposition, candidate_digest, target, policy_generation, "
					+ "recorded_at) VALUES (?, 'integration', ?, ?, 'integrated', ?, ?, "
					+ "NULL, ?)",
					integrationId, proposalId, actor, proposal.candidate_digest,
					proposal.target, new Date().toISOString());
				return { kind: "integration", receiptId: integrationId, proposalId,
				         actor, disposition: "integrated" };
			});
	}

	integrationAttempts(proposalId) {
		return this.#store.all(
			"SELECT * FROM integration_attempt WHERE proposal_id = ? ORDER BY seq",
			proposalId);
	}

	// -- close -------------------------------------------------------------

	// Ruling 4. Authorized UNCLAIMED closure is preserved — no execution
	// claim is manufactured merely to reach a terminal state — while a
	// close that ends a live v12 assignment must supply and compare its
	// full exact identity.
	//
	// Review 2026-08-22 [P1]: §7 says an AUTHORIZED actor holding the
	// configured close capability, and this method had neither an actor nor
	// a check. Both close forms now name their actor: the exact-assignment
	// form still compare-and-swaps the identity, and holding the assignment
	// is not by itself authority to terminalize the Work.
	close({ workId, outcome, rationale, actor, operationId, expect = undefined }) {
		// One snapshot, validated once. The session snapshots too; this is
		// the same guarantee for a caller that reached the core another
		// way, and it is where `expect` stops being caller-owned.
		expect = normalizeAssignment(expect);
		return this.#store.replay(
			operationId,
			signatureOf("close", { workId, outcome, rationale, actor, expect }),
			() => {
				this.#requireCapability(actor, "close", "close");
				const work = this.#work(workId);
				if (work.status !== "open") throw new Refusal("Work is already closed");
				if (!INTAKE_OUTCOMES.has(outcome)) throw new Refusal(`unknown outcome ${outcome}`);
				if (!rationale) throw new Refusal("close needs a non-empty rationale");
				const live = this.assignmentOf(workId);
				if (live !== null && expect === undefined) {
					throw new Refusal(
						"a close that ends a live assignment must supply its exact "
						+ "assignment identity");
				}
				if (expect !== undefined) this.#expect(expect);
				if (live !== null) {
					// `phase: null` is TERMINAL, not a scheduler state: a closed
					// Work has no phase at all. `#assertPhaseGate` accepts it for
					// exactly this caller and rejects a gate beside it.
					this.#endAssignment(expect, {
						phase: null, gate: null, cause: `close:${outcome}`, fence: true,
						reason: rationale,
					});
				}
				this.#store.run(
					"UPDATE work SET status = 'closed', phase = NULL, gate = NULL, "
					+ "outcome = ?, rationale = ? WHERE work_id = ?",
					outcome, rationale, workId);
				return { outcome, actor, assignment: live };
			});
	}

	// -- invariants --------------------------------------------------------

	// §10, asserted against the durable rows rather than against anything
	// this process remembers. Tests call it after every scenario, and it is
	// cheap enough that a caller may leave it on.
	assertInvariants(workId) {
		const work = this.#work(workId);
		const failures = [];
		const check = (ok, message) => { if (!ok) failures.push(message); };
		const held = work.handler !== null;
		const fenced = new Set(this.fencedGenerations(workId));
		if (held) {
			check(work.phase === "active", "a Work with a Handler must be active");
			check(work.status === "open", "a closed Work cannot have a Handler");
			if (work.contract === V11) {
				check(work.live_generation === null,
					"a v11 claim mints no generation");
			} else {
				check(work.live_generation === work.generation_counter,
					"the live generation must be the current counter");
				check(!fenced.has(work.live_generation),
					"a fenced generation is never the live generation");
			}
			check(this.slotHolder(work.handler) === workId,
				"the Handler must hold this Work's claim slot");
		} else {
			check(work.phase !== "active", "no Work is active without an executor");
			check(work.live_generation === null,
				"an unclaimed Work has no live assignment");
			check(this.#store.get(
				"SELECT 1 AS ok FROM claim_slot WHERE work_id = ?", workId) === undefined,
				"an unclaimed Work holds no participant's claim slot");
		}
		for (const generation of fenced) {
			check(generation >= 1 && generation <= work.generation_counter,
				`fenced generation ${generation} is outside the minted range`);
		}
		if (work.gate !== null) {
			check(work.phase === "block", "a gated Work is in phase block");
		}
		if (work.status !== "open") {
			check(work.phase === null && !held,
				"terminal Work has no phase and no Handler");
		}
		if (failures.length) {
			throw new Error(`v12 authority invariant violated for ${workId}: `
				+ failures.join("; "));
		}
		return true;
	}
}

// -- The two public faces ---------------------------------------------------
//
// Re-review 2026-08-22 [P1]. One object carried both the trusted bootstrap
// and the runtime consumer surface, and W2929 was directed to consume it.
// Through the advertised boundary alone, the reviewer claimed as
// `publisher`, called `grantCapability("publisher", "close")`, closed the
// live Work as that actor, and called
// `setPolicy("canonical_target", "unreviewed-tree")` — the canonical
// target moved with zero proposals and zero receipts. A second
// reproduction simply passed a configured closer's NAME, because the
// capability check compared a string the same caller supplied.
//
// A capability nobody can take away from you is not a capability, and an
// actor identity the caller chooses is not an identity. So they are now
// different objects:
//
//   V12Authority  the TRUSTED bootstrap. It configures — certifies
//                 contracts, permits transitions, grants capabilities,
//                 sets policy, creates Work — and it VENDS sessions. A
//                 deployment holds exactly one, at start-up.
//
//   V12Session    the RUNTIME boundary, bound at construction to one
//                 participant. It performs transitions and reads
//                 projections. It cannot configure anything, cannot reach
//                 the authority that made it, and cannot name a
//                 participant other than its own — the actor on every
//                 receipt and the claimant on every claim come from the
//                 binding, never from an operand.
//
// THE TRUST BOUNDARY IS THE FILESYSTEM, exactly as v11 states for its own
// authority: whoever can open the store file is the deployment. A session
// therefore carries no path, no store and no authority handle, and a
// deployment does not hand its manager the store path. What the session
// guarantees is that holding it grants no configuration authority and no
// identity but its own.

// Sessions are minted, never constructed. `PRIVATE` is module-local and
// exported nowhere, so a consumer that reaches the class through its own
// instance's prototype still cannot make a second one for another
// participant.
const PRIVATE = Symbol("v12-session-mint");

// What a session may do. Written out rather than derived, so adding a
// method to `Core` does not silently widen the runtime boundary: a new one
// is unreachable until somebody puts it here deliberately.
const SESSION_TRANSITIONS = [
	"activity", "advanceContract", "approve", "cancel", "close", "end",
	"installGate", "integrate", "pass", "publish", "rejectPlan", "review",
	"satisfyGate", "settleOperation", "verify",
];
// The transitions that WRITE an attributable actor. Only these receive one;
// the rest are authorized by the exact assignment they compare-and-swap, and
// handing them an operand they do not use would be noise that looks like
// authorization.
const ACTOR_TRANSITIONS = new Set(
	["approve", "close", "integrate", "review", "verify"]);

// One rule, applied by every session entry point including `claim`.
function assertNoIdentityOperand(what, operands) {
	for (const name of ["actor", "participant"]) {
		if (Object.hasOwn(operands, name)) {
			throw new Refusal(
				`${what} takes its actor from the session it is called on; `
				+ `supplying ${name} would let a caller choose an identity the `
				+ `authority then treated as authenticated`);
		}
	}
}
const SESSION_READS = [
	"assignmentOf", "assignmentEvents", "activities", "canonicalTarget",
	"contractEvents", "fencedGenerations", "gateEvidence", "integrationAttempts",
	"operationRecord", "operationResult", "projectWork", "proposal", "receipt",
	"receipts", "slotHolder", "assertInvariants",
];

export class V12Session {
	#core;
	#participant;

	constructor(mint, core, participant) {
		if (mint !== PRIVATE) {
			throw new Refusal(
				"a session is minted by the trusted authority, not constructed; "
				+ "holding one grants no way to make another");
		}
		this.#core = core;
		this.#participant = participant;
	}

	get participant() { return this.#participant; }

	// The claimant is the BINDING, not an operand. A session for
	// `poc.claude` cannot claim for anybody else, so there is no identity to
	// choose.
	claim(given = {}) {
		// Re-review 2026-08-22 [P2]: this destructured only `workId` and
		// `operationId`, so a supplied `participant` was silently ignored and
		// the caller could believe it had been honoured. Same rule as every
		// other transition — refused, not dropped.
		const operands = snapshot(given);
		assertNoIdentityOperand("claim", operands);
		return this.#core.claim({
			workId: operands.workId, participant: this.#participant,
			operationId: operands.operationId });
	}

	// The delegating methods are installed from INSIDE the class body, which
	// is the only place `#core` is in scope. That is deliberate: a method
	// added outside could not reach the core, which is the same reason a
	// consumer cannot.
	static {
		for (const name of SESSION_TRANSITIONS) {
			V12Session.prototype[name] = function (given = {}) {
				// SNAPSHOT FIRST, and never read the caller's object again.
				//
				// Re-review 2026-08-22 [P1]: this used to read
				// `operands.expect.participant` for the binding check and then
				// hand the SAME object to the core, which read it again. A getter
				// answering `poc.claude` twice and `poc.gemini` afterwards passed
				// the check and then ended Gemini's live assignment. Validating
				// one view and executing another is the defect; snapshotting is
				// the only thing that removes it.
				const operands = snapshot(given);
				// An operand that looks authoritative and is not is worse than no
				// operand, so supplying one is refused rather than ignored.
				assertNoIdentityOperand(name, operands);
				// A session acts only on its OWN assignments — for the
				// ASSIGNMENT-OWNED acts. The assignment identity authorizes those
				// and is not a secret, so a session that could act on somebody
				// else's would make the binding decorative.
				//
				// `close` is deliberately not one of them. §7 authorizes it by
				// the close CAPABILITY, and its mandatory `expect assignment` is
				// a compare-and-swap operand rather than proof of authorship: an
				// approver closing a Work somebody else is executing is the
				// ordinary case, and the identity is what stops them closing
				// blindly.
				const expect = ACTOR_TRANSITIONS.has(name) ? undefined : operands.expect;
				if (expect && typeof expect === "object" && expect.participant !== undefined
						&& expect.participant !== this.#participant) {
					throw new Refusal(
						`this session acts for ${this.#participant}; the assignment `
						+ `names ${expect.participant}`);
				}
				return this.#core[name](ACTOR_TRANSITIONS.has(name)
					? { ...operands, actor: this.#participant } : operands);
			};
		}
		for (const name of SESSION_READS) {
			V12Session.prototype[name] = function (...operands) {
				return this.#core[name](...operands);
			};
		}
	}
}

export class V12Authority {
	#core;

	constructor(core) { this.#core = core; }

	static create(path, { authorityUuid = randomUUID() } = {}) {
		return new V12Authority(new Core(Store.open(path, { authorityUuid })));
	}

	static open(path, options = {}) {
		return new V12Authority(new Core(Store.open(path, options)));
	}

	static claimSignature(workId, participant) {
		return Core.claimSignature(workId, participant);
	}

	// `dispose`, not `close`: `close` is the Baton verb that terminalizes a
	// Work, and one name for "release the file handle" and "end this Work
	// with an outcome" would be an API that invites the wrong one.
	dispose() { this.#core.dispose(); }

	get authorityUuid() { return this.#core.authorityUuid; }

	// Mint the narrow runtime handle for one participant. This is the only
	// route to a transition at all.
	session(participant) {
		if (typeof participant !== "string" || participant === "") {
			throw new Refusal("a session is bound to one named participant");
		}
		return new V12Session(PRIVATE, this.#core, participant);
	}

	// Configuration and read projections. The runtime face has none of the
	// first group, which is the whole point of there being two faces.
	static {
		for (const name of [
			"certifyContract", "withdrawCertification", "isCertified",
			"permitContractTransition", "permitsContractTransition", "setPolicy",
			"policy", "canonicalTarget", "setLookupAvailable", "grantCapability",
			"revokeCapability", "holdsCapability", "capabilitiesOf", "createWork",
			"addRouteHandler", "projectWork", "assignmentOf", "fencedGenerations",
			"slotHolder", "assignmentEvents", "contractEvents", "gateEvidence",
			"activities", "proposal", "receipts", "receipt", "integrationAttempts",
			"operationResult", "operationRecord", "assertInvariants",
		]) {
			V12Authority.prototype[name] = function (...operands) {
				return this.#core[name](...operands);
			};
		}
	}
}
