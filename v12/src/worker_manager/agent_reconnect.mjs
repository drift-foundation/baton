// W2929 plan item 4, seventh slice: RECONNECT AMBIGUITY.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// The pinned acceptance, frozen §8.4:
//
//   "A lost transport ENDS THE EPOCH. The relay never resumes and never
//    re-prompts."
//
// AND THE REASONING IS SPECIFIC RATHER THAN GENERAL CAUTION. A turn that was
// in flight when the transport died may have completed, partially completed,
// or not started — and it had a WRITABLE WORKSPACE. Re-prompting a fresh
// session with the same content would re-run side effects the manager cannot
// enumerate, against a workspace that already holds the first attempt's
// partial output. ACP 1.0 has no resumable turn: `session/load` and
// `session/resume` restore CONVERSATION, not an in-flight turn, and §2.3
// refuses them anyway — which the handshake slice already enforces.
//
// SO THE ANSWER IS THREE FACTS AND A REFUSAL. The turn outcome is
// `transport-lost` when one was in flight, the session state is `unknown`,
// and a new epoch is NOT allowed without positive runtime re-identification.
// The re-identification gate itself is W151 §9's and is deliberately not
// built here; this boundary's job is to say that it is required, which is the
// half that keeps a later slice from quietly skipping it.
//
// AND `unknown` IS WHY THE AXIS EXISTS. §3.3 and §7.3 make it terminal: it
// means no terminal fact was observed, and promoting it to `closed` would
// record knowledge nobody acquired. Transport loss is the ordinary way an
// epoch reaches it.

import { ContractError } from "./contracts.mjs";
import { classify, describe, isPlainRecord } from "./records.mjs";
import { normalizeAgentSessionRef, observeAgentSessionStateIn }
	from "./agent_session_axis.mjs";
import { requireSlotRecoveryIn } from "./posture_slots.mjs";

/*  THE RECORD PROOF LIVES IN `records.mjs` NOW.
 *
 *  Six review rounds on this boundary produced one rule — a document is data
 *  without behaviour — and the ACP capability envelope grew its own copy of
 *  it. Both copies were then found to have the SAME Proxy defect,
 *  independently, one round apart. W641's second review made unifying them a
 *  requirement rather than a follow-up, so `classify`, `describe` and
 *  `isPlainRecord` moved out whole; the history behind each rule moved with
 *  them and is in that module's header.
 *
 *  What stays here is what is SPECIFIC to this boundary: the member this
 *  contract expects, and the error taxonomy this boundary refuses in. The
 *  shared primitive returns facts and prose and never a `ContractError`,
 *  because `integrity.schema` here and `policy.denied` at the capability
 *  envelope are the callers' policies, not the primitive's. */

/** The caller's own `turnInFlight`, as DATA or not at all.
 *
 *  Fourth re-review [P2]: `hasOwnProperty` runs nothing, but the property
 *  READ that followed it executes an own ACCESSOR — so an accepted plain
 *  record could still run behaviour at a boundary whose whole rule is that it
 *  does not. An options document carries data; a getter is a program, and a
 *  program is not an operand.
 *
 *  Absence and a data descriptor are the two acceptable answers. Reflection
 *  failure translates rather than escaping, for the same reason the prototype
 *  snapshot does.
 *
 *  MEASURED: the accessor refusal is MASKED for the REFUSAL — an accessor's
 *  descriptor has no `value`, so the boolean proof downstream refuses it with
 *  the same pair. What the accessor branch adds is the message, and what
 *  actually keeps the getter from RUNNING is reading the descriptor instead
 *  of the property. That read is the guard; this branch is its explanation,
 *  and it is not counted as one. */
function ownTurnInFlight(options) {
	let descriptor;
	try {
		descriptor = Object.getOwnPropertyDescriptor(options, "turnInFlight");
	} catch {
		// Fifth review [P2]: this read `failure.message`. JavaScript lets a
		// throw carry ANY value, so the refusal interpolated a property of an
		// object the caller chose — an accessor there runs the caller's code
		// inside the refusal, and its own throw replaces the closed pair with
		// an arbitrary Error. A catch that establishes a refusal does not
		// interview the value that was thrown at it. The text below is the
		// manager's, and it is the same text whatever was thrown.
		throw new ContractError("integrity", "schema",
			`this transport-loss options document refused inspection; `
			+ `operands are read before anything durable happens, and a `
			+ `boundary that has decided to refuse does not read what was `
			+ `thrown at it`);
	}
	if (descriptor === undefined) return { present: false, value: false };
	if (!("value" in descriptor)) {
		throw new ContractError("integrity", "schema",
			`turnInFlight is an accessor on this options document; an operand `
			+ `is data, and reading a getter would run the caller's code at a `
			+ `boundary that decides an outcome`);
	}
	return { present: true, value: descriptor.value };
}

/** What a lost transport does to one epoch. §8.4.
 *
 *  Durable: the session axis moves to `unknown` through the axis boundary, so
 *  the full §3.1 reference is proved and bound exactly as every other
 *  observation is. Idempotent by the axis's own rule — a second report of the
 *  same loss re-observes `unknown` and answers rather than refusing, because
 *  a transport does not die twice differently.
 *
 *  IT REPORTS THE TURN OUTCOME AND DOES NOT RECORD IT. `recordTurn` needs an
 *  allocated turn token, a prompt digest and the supervision window, and this
 *  boundary holds none of them — inventing them to write a turn document here
 *  would be minting evidence about a turn it never saw. The caller records the
 *  turn with its own operands and this answer's outcome. */
export function handleTransportLoss(store, sessionRef, options) {
	// THE ENVELOPE BEFORE ANYTHING ELSE. Review [P1]: `{ ... } = {}` defaults
	// only for `undefined`, so an explicit `null` reached a property read and
	// left as a raw `TypeError` — and a boolean, a string or an array
	// destructured to `undefined`, silently took the `false` default, and
	// COMMITTED the epoch to `unknown` on operands nobody proved. A default
	// is for an absent argument, not for a wrong one.
	//
	// Re-review [P1]: and my first correction wrote that sentence and then
	// tested `typeof options === "object"`, which is true of a Date, a Map, a
	// regular expression and every class instance. Each of those took the
	// absent-member default and committed the epoch — the same defect the
	// paragraph above describes, surviving the fix aimed at it, because
	// "not a primitive and not an array" is not "is a record".
	//
	// A RECORD IS A PROTOTYPE TEST. Ordinary object literals and
	// `Object.create(null)` documents are records; anything carrying its own
	// class is a value with behaviour, and a caller handing this boundary one
	// has not handed it a document.
	const shape = options === undefined ? null : classify(options);
	if (options !== undefined && !isPlainRecord(options, shape)) {
		throw new ContractError("integrity", "schema",
			`${describe(options, shape)} is not a transport-loss options `
			+ `document; this call ends an epoch and its operands are proved `
			+ `before anything durable happens`);
	}
	// ABSENT, not falsy. `?? false` would turn an explicit `null` into the
	// default and make the wrong-argument case the missing-argument case —
	// the same mistake as the envelope above, one level down, and my own
	// earlier case caught it.
	//
	// AN OWN MEMBER, not an inherited one. Re-review [P1]: `in` walks the
	// prototype chain, so a document created over `{ turnInFlight: true }`
	// would have been read from something the caller never put in the
	// document it passed. What was GIVEN is what is on the object.
	const turnInFlight = options === undefined
		? false : ownTurnInFlight(options).value;
	if (typeof turnInFlight !== "boolean") {
		throw new ContractError("integrity", "schema",
			`${describe(turnInFlight)} is not whether a turn was in flight; `
			+ `this decides an outcome and is not inferred`);
	}
	// ONE SNAPSHOT, TAKEN ONCE. Review [P1]: the answer spread the caller's
	// object AFTER the axis had already validated and committed against its
	// own normalized copy — so a getter could answer provider A to the check
	// and provider B to the record, and members the closed reference shape
	// does not have rode along into the answer. The reference is proved here,
	// the SAME object goes to the axis, and the same object is reported.
	const ref = normalizeAgentSessionRef(sessionRef);
	// ONE ACT. Review [P1]: this recorded `unknown` and left the slot
	// occupied, so the durable result contradicted the ruling's "ambiguity
	// moves it to recovery-required" and bypassed the recovery API that
	// later positive runtime evidence is meant to discharge.
	//
	// Composing them through two transactions would leave a crash window in
	// which the observation had landed and the slot had not — a session
	// recorded `unknown` whose posture still looked live. One transaction,
	// so a crash leaves either both or neither.
	const db = store.db;
	db.exec("BEGIN IMMEDIATE");
	let observed;
	let occupancy;
	try {
		observed = observeAgentSessionStateIn(db, ref, "unknown");
		// THE OBSERVATION IS ABOUT THIS EPOCH AND ALWAYS LANDS. The slot
		// movement is about the posture, and a posture a later epoch has
		// taken — or one already recovered on positive evidence — is not
		// this report's to move.
		//
		// Re-review [P1]: this required both, so a retry after recovery
		// refused on `available` and a delayed epoch-1 report refused on
		// epoch 2 and left epoch 1 falsely `ready`. The transport really did
		// die for THIS epoch, and that is true whatever the posture has done
		// since. The reviewer taught me this asymmetry for `closeAgentSession`
		// last round; I applied it there and not one function over.
		const held = db.prepare(
			"SELECT occupancy, session_epoch FROM posture_slots WHERE "
			+ "runtime_attempt_id = ? AND posture = ?")
			.get(ref.runtimeAttemptId, ref.posture);
		const mine = held !== undefined
			&& held.session_epoch === ref.sessionEpoch;
		occupancy = mine && held.occupancy === "occupied"
			? requireSlotRecoveryIn(db, store.clock(), {
				attemptId: ref.runtimeAttemptId, posture: ref.posture,
				sessionEpoch: ref.sessionEpoch,
				reason: "the transport died and nothing observed the ending",
			}).occupancy
			: held?.occupancy ?? null;
		db.exec("COMMIT");
	} catch (failure) {
		try { db.exec("ROLLBACK"); } catch { /* already settled */ }
		throw failure;
	}
	return {
		// MEASURED AS EQUIVALENT, and said rather than implied: `ref` is
		// created by `normalizeAgentSessionRef` and nothing else holds it,
		// so returning it directly passes every case. The copy is kept
		// because a boundary that hands back the object it validated against
		// is one edit away from handing back the object it is still using,
		// and it is not counted as a guard.
		agentSessionRef: { ...ref },
		sessionState: observed.state,
		// The two refusals §8.4 names, reported as facts rather than left to
		// a caller's memory of the section.
		// THE OCCUPANCY THAT ACTUALLY HOLDS, not the one this report
		// would have produced on its own.
		slotOccupancy: occupancy,
		resume: false,
		reprompt: false,
		nextEpochAllowedWithoutRuntimeReidentification: false,
		turnOutcome: turnInFlight ? "transport-lost" : null,
	};
}

/** §8.4 — re-prompting after transport loss is refused, always.
 *
 *  `ambiguous.operation` and not `refused.precondition`: the manager is not
 *  saying the request is malformed or out of order, it is saying it CANNOT
 *  KNOW what the first attempt did. That is the whole content of the refusal,
 *  and the closed pair carries it to a caller that never read §8.4.
 *
 *  It takes the prompt and ignores it deliberately. A signature that accepted
 *  nothing would invite a caller to believe some other prompt might be
 *  acceptable; the refusal is about the epoch, not about what is being
 *  re-sent. */
export function repromptAfterTransportLoss(_prompt) {
	throw new ContractError("ambiguous", "operation",
		`a turn in flight when the transport died may have run side effects `
		+ `the manager cannot enumerate, against a workspace that already `
		+ `holds the first attempt's partial output; re-prompting is refused `
		+ `and a new epoch waits for positive runtime re-identification`);
}

/** §8.4 — transport reachability returning is not the runtime being the same
 *  runtime.
 *
 *  The one function here that always answers false, for the same reason
 *  §7.4's quiescence gate does: a fact about a socket is not a fact about the
 *  process that held the generation. W151 §9's re-identification is what
 *  answers this, and it is not built in this slice — so this says so rather
 *  than leaving a later caller to assume reachability was enough. */
export function transportReachabilityReidentifies(_evidence) {
	return false;
}
