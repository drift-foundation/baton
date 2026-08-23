// W2929 plan item 3, first half: the OFFER and the CLAIM.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/`
//
// This is the boundary where a manager spends a bearer and takes a claim on
// somebody's behalf, so every step here is about ONE question: after a crash,
// can the next incarnation tell what actually happened?
//
// The pinned cuts, in order, and each one is a durable fact rather than an
// inference:
//
//   1. read the Work and the participant's capacity BEFORE spending entropy;
//   2. one control-store transaction wins the per-Work offer CAS and stores
//      the VERIFIER — the bearer is emitted only after that commit;
//   3. acceptance validates the envelope before any field, compares the
//      binding and the verifier in constant time, and in ONE transaction
//      consumes the verifier, freezes the intent digest, derives the fixed
//      claim operation id and stores a SEPARATE settlement deadline;
//   4. the claim is submitted through the participant-bound session and its
//      result is recorded before anything else may run;
//   5. a LOST result is settled through the authority's own
//      `settleOperation`, which may only OBSERVE before the deadline;
//   6. a commit the manager never saw is recorded late, on restart.
//
// WHAT IS NOT HERE, and it is the rest of item 3: assignment activation,
// runtime start and reconciliation, the orthogonal observation axes,
// cancellation ordering, output freeze and intake, and cleanup. Item 4 —
// agent-session normalization and the adapter contracts — is untouched.

import { randomUUID } from "node:crypto";

import { assertNoDurableSecret, ContractError, digest, tokenVerifier,
         validateOfferDecide, withSecret } from "./contracts.mjs";
// The authority's OWN derivation of the claim signature. Imported rather
// than restated: a third copy of a signature rule is a third thing that can
// drift, and this one decides whether a settlement is recognised at all.
import { V12Authority } from "../authority/authority.mjs";

// §10.2: capacity is advisory here and decided again inside the authority's
// claim transaction. Checking it at issue is not a substitute — it is what
// stops a manager minting a bearer it can already see it cannot spend.
export const OFFER_TTL_MS = 120_000;
export const SETTLE_MS = 60_000;

const NONTERMINAL = new Set(["issued", "accepted"]);

function instant(clock) { return clock(); }

function later(from, milliseconds) {
	return new Date(Date.parse(from) + milliseconds).toISOString();
}

/** The one deterministic claim operation id for an accepted offer.
 *
 *  DERIVED, never random. It is what makes a lost result settleable: the
 *  next incarnation must be able to name the exact operation this one
 *  submitted without having seen it submitted. */
export function claimOperationId(offerId, intentDigest) {
	return `claim:${digest({ offerId, intentDigest }).slice("sha256:".length)}`;
}

/** The control store's own certification for one profile digest, if any.
 *
 *  A withdrawn profile is not certified — that is what withdrawal means —
 *  so the row is only an answer while `withdrawn_at` is null. */
function certifiedProfile(store, profileDigest) {
	// SCOPED TO THE RUNTIME AXIS. Review [P1]: this asked only for the digest,
	// so a genuinely certified AGENT-SESSION profile satisfied an offer's
	// RUNTIME profile check. The two are separate contract axes with separate
	// schemas, seals and policies; a digest certified under one is not
	// certification under the other even when the bytes are genuine, and
	// "certified" without a kind is a question that does not have one answer.
	const row = store.db.prepare(
		"SELECT digest FROM profiles WHERE kind = 'runtime' AND digest = ? "
		+ "AND withdrawn_at IS NULL").get(profileDigest);
	return row?.digest ?? null;
}

/** Settle every offer whose TTL has elapsed.
 *
 *  Manager-owned: it needs no message from anybody, which is the whole
 *  point. Scoped to one Work when reissuing that Work, and unscoped from
 *  restart recovery, where every elapsed offer is equally stale.
 *
 *  An offer that another act settles first is not an error here — this is
 *  housekeeping, and losing its CAS means somebody else already did it. */
export function expireOverdue(store, { workId = null, now = null } = {}) {
	const at = now ?? instant(store.clock);
	const rows = workId === null
		? store.db.prepare(
			"SELECT * FROM offers WHERE state='issued' AND expires_at <= ?")
			.all(at)
		: store.db.prepare(
			"SELECT * FROM offers WHERE state='issued' AND work_id = ? "
			+ "AND expires_at <= ?").all(workId, at);
	const expired = [];
	for (const offer of rows) {
		if (expireOffer(store, offer, at) !== null) expired.push(offer.offer_id);
	}
	return expired;
}

/** Record one certified RUNTIME profile. The manager certifies locally;
 *  nothing here reaches a provider.
 *
 *  Review [P1]: this took `kind` as an operand and accepted `agent-session`,
 *  writing a caller-authored digest straight into the same table — so the
 *  agent-session shape, seal, posture-policy and secret checks were
 *  avoidable by not calling the entry point that performs them. One
 *  composing route per kind, or the route is a suggestion.
 *
 *  THE OPERAND IS REFUSED RATHER THAN IGNORED, and that is a deliberate
 *  choice with a hazard behind it: silently dropping a supplied
 *  `agent-session` would turn an attempted agent-session forgery into a
 *  SUCCESSFUL RUNTIME one, certifying a digest the caller never meant to
 *  offer to that axis. An operand that looks authoritative and is not is
 *  worse than no operand — the same rule the authority's sessions already
 *  apply to `participant`. */
export function certifyRuntimeProfile(store, given = {}) {
	if (Object.hasOwn(given, "kind")) {
		throw new ContractError("integrity", "schema",
			"this writer certifies RUNTIME profiles and takes no kind; an "
			+ "agent-session profile is certified by composing shape, seal "
			+ "and policy, which naming a kind here would bypass");
	}
	const { name, digest: value, at = null } = given;
	store.db.prepare(
		"INSERT INTO profiles (kind, name, digest, certified_at) "
		+ "VALUES ('runtime', ?, ?, ?) ON CONFLICT(kind, name) DO UPDATE SET "
		+ "digest = excluded.digest, certified_at = excluded.certified_at, "
		+ "withdrawn_at = NULL")
		.run(name, value, at ?? store.clock());
	return { kind: "runtime", name, digest: value };
}

function offerRow(store, offerId) {
	return store.db.prepare("SELECT * FROM offers WHERE offer_id = ?")
		.get(offerId) ?? null;
}

/** Step 1 and 2: issue one offer, and mint the bearer only after the commit.
 *
 *  The reads happen BEFORE entropy is spent because a bearer that is minted
 *  and then refused is a secret that existed for no reason — and the
 *  per-Work CAS is the database's, not a read-then-write check, because two
 *  manager processes both pass any check made outside the write. */
export function issueOffer(store, session, {
		workId, participant, runtimeAttemptId = randomUUID(),
		offerId = randomUUID(), inputDigest, policyDigest, profileDigest,
		certifiedProfileDigest, readinessEpisode = null,
		ttlMs = OFFER_TTL_MS, mintBearer = () => randomUUID() + randomUUID(),
	}) {
	// THE PARTICIPANT IS THE SESSION'S BINDING, not an operand beside it.
	//
	// Review [P1]: this took `participant` independently and never compared
	// it. The offer, the verifier and the intent could name B while
	// `submitClaim` necessarily acts as A through the bound session — an
	// authorization recorded for one identity and spent by another.
	if (session.participant === undefined || session.participant === null) {
		throw new ContractError("integrity", "schema",
			"an offer is issued through a participant-bound session; this one "
			+ "names no participant, so nothing binds the authorization it "
			+ "records to the identity that will spend it");
	}
	if (participant !== undefined && participant !== session.participant) {
		throw new ContractError("refused", "precondition",
			`the offer names ${participant} and this session acts for `
			+ `${session.participant}; the claim would be taken by the `
			+ `binding, not by the operand`);
	}
	participant = session.participant;
	const work = session.projectWork(workId);
	if (work.status !== "open" || work.phase !== "queued"
			|| work.handler !== null || work.gate !== null) {
		throw new ContractError("refused", "precondition",
			`${workId} is ${work.status}/${work.phase} with handler `
			+ `${work.handler} and gate ${work.gate?.token ?? null}; an offer `
			+ `is issued only against open, queued, unclaimed, ungated Work`);
	}
	// CERTIFICATION IS UNAVOIDABLE.
	//
	// Review [P1]: the comparison was conditional on the argument being
	// supplied, so OMITTING it issued an offer with no certification check
	// at all — and the happy-path fixtures omitted it throughout. A check a
	// caller can skip by not mentioning it is not a boundary.
	//
	// The control store's own `profiles` row is the stronger fact and is
	// preferred when it exists; an explicit operand is accepted otherwise
	// and may not CONTRADICT the store. Absence of both is refused, before
	// entropy.
	const certified = certifiedProfile(store, profileDigest);
	const asserted = certified ?? certifiedProfileDigest;
	if (asserted === undefined || asserted === null) {
		throw new ContractError("policy", "profile-uncertified",
			`nothing certifies profile ${profileDigest} for this manager; an `
			+ `offer promises an execution shape, and one nothing has agreed `
			+ `to is not a shape`);
	}
	if (certified !== null && certifiedProfileDigest !== undefined
			&& certifiedProfileDigest !== certified) {
		throw new ContractError("policy", "profile-uncertified",
			`the caller asserts ${certifiedProfileDigest} and the control `
			+ `store certifies ${certified}`);
	}
	if (asserted !== profileDigest) {
		throw new ContractError("policy", "profile-uncertified",
			`the offer names profile ${profileDigest} and this manager has `
			+ `certified ${asserted}`);
	}
	// ELAPSED OFFERS ARE SETTLED BY THE MANAGER'S OWN CLOCK.
	//
	// Re-review [P1]: expiry was reachable only from a LATE DECISION, so an
	// offer whose worker never answered stayed `issued` with an unspent
	// verifier and held the per-Work unique index forever. A bound that
	// depends on the holder of an expired authorization sending one more
	// message is not a bound. Reissue is manager-owned time processing, and
	// it is where this belongs — before entropy, like every other check.
	expireOverdue(store, { workId });
	const held = session.slotHolder(participant);
	if (held !== null && held !== undefined) {
		throw new ContractError("refused", "precondition",
			`${participant} already holds ${held}; capacity is checked here `
			+ `so a bearer is not minted for a claim that cannot be taken, `
			+ `and again inside the authority's own transaction (§10.2)`);
	}
	const issuedAt = instant(store.clock);
	// EVERY EFFECTIVE DURABLE OPERAND rides the signature.
	//
	// Review [P1]: it covered only `(offerId, workId, participant)`, so a
	// changed policy digest REPLAYED the first offer as though it were the
	// same request. An operation identity that ignores operands is not an
	// identity.
	// THE FULL AUTHORITY-SCOPED BINDING, not the local Work id alone.
	//
	// Re-review [P1]: the signature carried `workId` while the row persists
	// `authority_uuid` too, so reusing an issue identity against ANOTHER
	// authority read as an exact replay rather than an operation collision.
	// A changed durable operand is not an exact replay, and the authority a
	// Work belongs to is as durable as the Work.
	const signature = digest({ kind: "offer.issue", operands: {
		offerId, authorityUuid: work.authorityUuid, workId, participant,
		runtimeAttemptId, inputDigest, policyDigest, profileDigest,
		readinessEpisode, expiresAt: later(issuedAt, ttlMs) } });
	// AND THE REPLAY IS CHECKED BEFORE ENTROPY IS SPENT.
	//
	// Review [P1]: the bearer was minted first, so an exact replay returned
	// the FIRST offer's durable verifier beside a newly minted bearer that
	// does not derive it — a secret the holder cannot use and cannot tell is
	// unusable. The bearer exists only in the process that minted it, so a
	// replay cannot reproduce it; refusing is the only honest answer, and it
	// is given without minting anything.
	if (store.replay(`offer.issue:${offerId}`, signature).found) {
		throw new ContractError("refused", "precondition",
			`offer ${offerId} is already issued; its bearer existed only in `
			+ `the process that minted it, so this call cannot reproduce one `
			+ `and will not return a bearer that does not derive the stored `
			+ `verifier`);
	}
	const bearer = mintBearer();
	const verifier = tokenVerifier(bearer);
	// THE ACTION IS THE COMMIT MARKER.
	//
	// Re-review [P1]: provenance was inferred from bearer INEQUALITY, and
	// inequality proves a loss while equality proves nothing — two exact
	// issuers can receive the same injected bearer, and the loser then
	// replayed the winner's record and reported success. Effectively-once
	// is decided by the journal, never by a probabilistic property of the
	// secret source.
	//
	// `transact` runs the action only when it did NOT replay, so the action
	// setting this flag IS the transaction boundary reporting which of the
	// two happened. Nothing about the payload is consulted.
	let committed = false;
	const record = store.transact(`offer.issue:${offerId}`, "offer.issue",
		signature, (db) => {
			committed = true;
			db.prepare(
				"INSERT INTO offers (offer_id, work_id, authority_uuid, "
				+ "participant, runtime_attempt_id, incarnation, "
				+ "readiness_episode, input_digest, policy_digest, "
				+ "profile_digest, verifier, issued_at, expires_at, state) "
				+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'issued')")
				.run(offerId, workId, work.authorityUuid, participant,
				     runtimeAttemptId, store.incarnation, readinessEpisode,
				     inputDigest, policyDigest, profileDigest, verifier,
				     issuedAt, later(issuedAt, ttlMs));
			return { offerId, workId, participant, runtimeAttemptId,
			         verifier, issuedAt, expiresAt: later(issuedAt, ttlMs) };
		});
	// AND THE DECIDING REPLAY IS THE ONE INSIDE THE TRANSACTION.
	//
	// Re-review [P1]: the optimistic check above answers the sequential
	// case, and two concurrent exact issuers both pass it. The winner
	// commits its verifier; `transact` then hands the LOSER that committed
	// record, and returning it beside the loser's freshly minted bearer is
	// the original unusable pair — under exactly the concurrency the
	// operation journal exists to settle.
	//
	// So the record is checked against the bearer this call minted. If it
	// does not derive it, this call lost, and the honest answer is a refusal
	// with no secret in it.
	if (!committed) {
		throw new ContractError("refused", "precondition",
			`offer ${offerId} was issued concurrently by another act; this `
			+ `call replayed that act's committed record rather than `
			+ `performing one, and the bearer it would answer with existed `
			+ `only in the process that minted it`);
	}
	// A SEPARATE INVARIANT, not the provenance decision. If this call did
	// commit, the row it just wrote must derive from the bearer it just
	// minted — anything else is a store defect, and returning a secret that
	// does not open the offer it names would be the worst kind.
	if (record.verifier !== verifier) {
		throw new ContractError("integrity", "digest",
			`offer ${offerId} committed a verifier this call's bearer does `
			+ `not derive`);
	}
	// The bearer rides back with the RESULT and never through the store.
	// `assertNoDurableSecret` already refused it at the journal boundary;
	// this is the other half of that rule — it is returned, not recorded.
	return { ...record, bearer };
}

/** Step 3: accept one decision, in one transaction.
 *
 *  The envelope and its body digest are validated by the caller's contract
 *  entry before this sees a field — that is the round-2 lesson and it is not
 *  re-litigated here. What this owns is the BINDING: the decision must name
 *  this exact offer, attempt and Work, and carry this exact verifier. */
export function acceptOffer(store, { offerId, body, now = null }) {
	const issued = offerRow(store, offerId);
	if (issued === null) {
		throw new ContractError("refused", "precondition",
			`no offer ${offerId}`);
	}
	const at = now ?? instant(store.clock);
	// §12 rule 14, on the product path. `validateOfferDecide` proves the
	// decision names ONE issued offer; the verifier proves possession.
	// The VERIFIER is passed too, so possession is proven by the contract
	// module that owns the derivation — and in constant time, which a second
	// comparison here would have undone.
	validateOfferDecide(body, {
		offer_id: issued.offer_id,
		runtime_attempt_id: issued.runtime_attempt_id,
		work_ref: { authority_uuid: issued.authority_uuid,
		            work_id: issued.work_id },
		verifier: issued.verifier,
		verifier_unspent: issued.verifier_spent === 0,
	});
	if (issued.state !== "issued") {
		throw new ContractError("refused", "already-terminal",
			`offer ${offerId} is ${issued.state}`);
	}
	if (at >= issued.expires_at) {
		// EXPIRY IS A SETTLEMENT, not only a refusal.
		//
		// Review [P1]: this threw and left the row `issued` with an unspent
		// verifier holding the per-Work slot — so the Work could never
		// receive another offer and the bearer stayed replayable, against
		// the pinned single-use rule. The row is settled first and the
		// refusal is still raised, because the caller's decision did fail.
		expireOffer(store, issued, at);
		throw new ContractError("refused", "precondition",
			`offer ${offerId} expired at ${issued.expires_at}`);
	}
	// A DECLINE terminates without spending anything else. The verifier is
	// still consumed: single-use across acceptance, decline and expiry
	// alike, so a decline cannot be replayed into an acceptance.
	if (body.decision === "decline") {
		return settleTerminal(store, issued, "declined", body.reason, at);
	}
	// The INTENT is frozen here and never rewritten: it is what the claim
	// operation id is derived from, so a later incarnation deriving the same
	// id must be looking at the same intent.
	const intentDigest = digest({
		offerId, workId: issued.work_id, participant: issued.participant,
		runtimeAttemptId: issued.runtime_attempt_id,
		inputDigest: issued.input_digest, policyDigest: issued.policy_digest,
		profileDigest: issued.profile_digest, acceptedAt: at,
	});
	const operationId = claimOperationId(offerId, intentDigest);
	// THE AUTHORITY'S OWN FIXED SIGNATURE, frozen with the intent.
	//
	// Review [P1]: this stored NULL, so settlement passed `undefined` — an
	// operation collision against a real committed claim, and a value the
	// authority's NOT NULL column cannot hold when retiring. A settlement
	// that cannot name its operation's operands cannot settle anything.
	const claimSignature = V12Authority.claimSignature(
		issued.work_id, issued.participant);
	const signature = digest({ kind: "offer.accept",
	                           operands: { offerId, intentDigest } });
	return store.transact(`offer.accept:${offerId}`, "offer.accept", signature,
		(db) => {
			const changed = db.prepare(
				"UPDATE offers SET state='accepted', verifier_spent=1, "
				+ "intent_digest=?, accepted_at=?, settle_by=?, "
				+ "claim_operation_id=?, claim_signature=? "
				+ "WHERE offer_id=? AND state='issued' AND verifier_spent=0")
				.run(intentDigest, at, later(at, SETTLE_MS), operationId,
				     claimSignature, offerId).changes;
			if (changed !== 1) {
				// The CAS lost. Another process accepted, declined or
				// expired this offer between the read and this write, and
				// the read's answer is not the one that counts.
				throw new ContractError("refused", "precondition",
					`offer ${offerId} was settled by another act`);
			}
			return { offerId, state: "accepted", intentDigest,
			         claimOperationId: operationId,
			         claimSignature, acceptedAt: at,
			         settleBy: later(at, SETTLE_MS) };
		});
}

/** An ISSUED-ONLY terminal transition: decline, expiry, abandonment.
 *
 *  Review [P1]: this updated `issued` OR `accepted` rows, and both callers
 *  act from an earlier `issued` read. Another manager can accept in
 *  between — and a stale decline or abandonment then destroyed the durable
 *  authorization and the fixed claim identity that acceptance had just
 *  frozen. Each of these transitions CASes only from `issued`, and losing
 *  the CAS reports the winner's state without rewriting it. */
function settleTerminal(store, issued, state, reason, at) {
	const signature = digest({ kind: `offer.${state}`,
	                           operands: { offerId: issued.offer_id, reason } });
	return store.transact(`offer.${state}:${issued.offer_id}`,
		`offer.${state}`, signature, (db) => {
			const changed = db.prepare(
				"UPDATE offers SET state=?, verifier_spent=1, "
				+ "decision_reason=?, decided_at=? "
				+ "WHERE offer_id=? AND state='issued'")
				.run(state, reason ?? null, at, issued.offer_id).changes;
			if (changed !== 1) {
				const now = db.prepare(
					"SELECT state FROM offers WHERE offer_id=?")
					.get(issued.offer_id);
				throw new ContractError("refused", "precondition",
					`offer ${issued.offer_id} is ${now?.state ?? "absent"}; a `
					+ `${state} decided from a stale read does not overwrite `
					+ `the state that won`);
			}
			return { offerId: issued.offer_id, state, reason: reason ?? null,
			         decidedAt: at };
		});
}

/** Expiry, settled by the same issued-only CAS. Separate from
 *  `settleTerminal` only so its operation identity names expiry rather than
 *  borrowing a decision's. */
function expireOffer(store, issued, at) {
	try {
		return settleTerminal(store, issued, "expired",
			`expired at ${issued.expires_at}`, at);
	} catch (failure) {
		// Losing this CAS is ordinary: another act settled the offer first,
		// and the caller's own refusal is what it came for.
		if (failure instanceof ContractError) return null;
		throw failure;
	}
}

/** Step 4: submit the ONE fixed claim through the participant-bound session.
 *
 *  The bearer is held for exactly this act — `withSecret` releases when the
 *  act settles, including when it throws — so a durable write during the
 *  claim cannot carry it even by accident.
 *
 *  The result is recorded BEFORE anything else may run. A manager that
 *  activated an assignment it had not durably recorded would have no way,
 *  after a crash, to tell an activation it performed from one it did not. */
export function submitClaim(store, session, { offerId, bearer = null }) {
	const offer = requireAccepted(store, offerId);
	const act = () => session.claim({ workId: offer.work_id,
	                                  operationId: offer.claim_operation_id });
	const result = bearer === null ? act() : withSecret(bearer, act);
	// THE ASSIGNMENT IS WHAT THE AUTHORITY RETURNED, not a member of it.
	//
	// Review [P1]: this read `result.assignment`, and `V12Session.claim`
	// returns the assignment directly — so the authority held a live
	// generation while the manager durably recorded `assignment: null`. A
	// record that disagrees with the authority is worse than no record: a
	// restart trusts it.
	return recordClaim(store, offer, "claimed", { assignment: result ?? null });
}

function requireAccepted(store, offerId) {
	const offer = offerRow(store, offerId);
	if (offer === null || offer.state !== "accepted") {
		throw new ContractError("refused", "precondition",
			`offer ${offerId} is ${offer?.state ?? "absent"}, not accepted`);
	}
	return offer;
}

function recordClaim(store, offer, state, detail) {
	const signature = digest({ kind: "offer.settle",
	                           operands: { offerId: offer.offer_id, state } });
	return store.transact(`offer.settle:${offer.offer_id}`, "offer.settle",
		signature, (db) => {
			const changed = db.prepare(
				"UPDATE offers SET state=?, decision_reason=?, decided_at=?, "
				// The GENERATION the claim committed. An attempt's
				// activation compares against this: a live assignment
				// somewhere in the authority is not proof that this offer
				// claimed it.
				+ "claim_generation=? WHERE offer_id=? AND state='accepted'")
				.run(state, detail.reason ?? null, instant(store.clock),
				     detail.assignment?.generation ?? null,
				     offer.offer_id).changes;
			if (changed !== 1) {
				throw new ContractError("refused", "already-terminal",
					`offer ${offer.offer_id} is no longer accepted`);
			}
			return { offerId: offer.offer_id, state, ...detail };
		});
}

/** Step 5: settle a claim whose result this manager never saw.
 *
 *  BEFORE THE DEADLINE IT MAY ONLY OBSERVE. That is the whole shape of this
 *  step: a read saying "not committed" proves only its own instant, because
 *  a submitter may already have passed its preconditions and be about to
 *  commit. So retiring early could close an identity the authority is still
 *  going to honour, and the manager would record a refusal for a claim that
 *  succeeded.
 *
 *  At or after the deadline, retirement is safe because the submitter's own
 *  window is over. POSITIVE EVIDENCE that the submitted claim refused
 *  permits immediate retirement — that is not a guess, it is the answer.
 *
 *  Every path ADOPTS an existing retirement's bound disposition and reason:
 *  whoever retired the identity first decided what it means, and a second
 *  manager inventing its own answer would give one operation two meanings. */
export function settleClaim(store, session, {
		offerId, now = null, refusedEvidence = null }) {
	const offer = requireAccepted(store, offerId);
	const at = now ?? instant(store.clock);
	const past = at >= offer.settle_by;
	const mayRetire = past || refusedEvidence !== null;
	const disposition = refusedEvidence !== null
		? "claim-refused" : "settlement-expired";
	const answer = session.settleOperation({
		operationId: offer.claim_operation_id,
		// The signature acceptance froze. Passing anything else — including
		// nothing — is an operation collision against a real committed claim.
		signature: offer.claim_signature,
		reason: refusedEvidence ?? "the manager lost this claim's result",
		disposition, mayRetire });
	if (answer.kind === "committed") {
		// STEP 6: the authority committed and this manager never saw it.
		// Recording it late is the whole reason the operation id is derived.
		return recordClaim(store, offer, "claimed",
			{ assignment: answer.result ?? null, late: true });
	}
	if (answer.kind === "retired") {
		// Adopt the BOUND answer, whoever bound it.
		const bound = answer.record ?? {};
		const state = bound.disposition === "claim-refused"
			? "claim-refused" : "settlement-expired";
		return recordClaim(store, offer, state, { reason: bound.reason ?? null,
		                                          adopted: true });
	}
	if (answer.kind === "refused") {
		return recordClaim(store, offer, "claim-refused",
			{ reason: answer.detail ?? null });
	}
	// `live`: the identity is still open and the deadline has not passed.
	// Nothing changes, and saying so is the honest answer — a control row
	// written here would claim knowledge this manager does not have.
	return { offerId, state: "accepted", settled: false,
	         why: `before ${offer.settle_by}; a lost result may only be `
	              + `observed, never retired` };
}

/** The restart rules, and they are deliberately asymmetric.
 *
 *  An ISSUED offer from a prior incarnation is not accepted after restart:
 *  nothing durable says the bearer was ever delivered, and a manager that
 *  honoured it would be trusting a secret it cannot account for. It stays
 *  VISIBLE until expiry or an explicit abandonment, its verifier is
 *  consumed, and a later offer uses a new bearer.
 *
 *  An ACCEPTED offer IS recoverable, because its authorization and its fixed
 *  claim operation are durable — that is what acceptance froze.
 *
 *  AND ONLY THIS INCARNATION'S. Several managers coordinate through the
 *  shared store, so abandoning an offer merely because this process did not
 *  mint its bearer would let one live manager destroy another's work. */
export function recoverOnRestart(store, { now = null } = {}) {
	const at = now ?? instant(store.clock);
	// Elapsed offers are settled first, so recovery reports what is really
	// live rather than counting rows the clock has already ended.
	expireOverdue(store, { now: at });
	const rows = store.db.prepare(
		"SELECT * FROM offers WHERE state IN ('issued', 'accepted') "
		+ "ORDER BY issued_at").all();
	const abandoned = [];
	const recoverable = [];
	for (const offer of rows) {
		if (offer.state === "accepted") {
			recoverable.push({ offerId: offer.offer_id,
			                   claimOperationId: offer.claim_operation_id,
			                   settleBy: offer.settle_by });
			continue;
		}
		if (offer.incarnation === store.incarnation) continue;
		settleTerminal(store, offer, "abandoned-after-restart",
			`issued by incarnation ${offer.incarnation}`, at);
		abandoned.push(offer.offer_id);
	}
	return { abandoned, recoverable };
}

/** Nothing this module returns may carry a durable secret except the one
 *  deliberate bearer, and that one is returned rather than stored. */
export function assertOfferSafe(record) {
	const { bearer: _bearer, ...rest } = record ?? {};
	assertNoDurableSecret(rest, "an offer record");
	return record;
}
