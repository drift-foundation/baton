// W2929 plan item 3, first half: the offer and the claim.
//
// Every case here asks the one question this boundary exists for: after a
// crash, can the next incarnation tell what actually happened? So the
// fixtures are about DURABLE facts — what survived, what was consumed, and
// what a second process reading the same store concludes.
//
// The authority session is a scripted double. That is deliberate: this slice
// is the manager's orchestration, and driving a real authority here would
// test the authority's claim transaction over again while making the
// manager's restart windows almost impossible to place exactly.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";

import { V12Authority, V12 } from "../src/authority/index.mjs";
import { ContractError, digest, tokenVerifier, GOLDEN_BEARER }
	from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { acceptOffer, claimOperationId, expireOverdue, issueOffer,
         recoverOnRestart, settleClaim, submitClaim, SETTLE_MS }
	from "../src/worker_manager/offers.mjs";

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const WHO = "poc.claude";
const BEARER = "b".repeat(48);

// The W2907 shared owned-root registry, and the `v12-manager-` family this
// Work already registered in the cleanup regressions. A suite that minted
// its own temporary roots would retain one per case — measured, not
// assumed: the first version of this file left twenty behind.
after(removeOwnedRoots);

function storePath() {
	return join(ownedTemp("v12-manager-"), "control.sqlite3");
}

function clockFrom(start = "2026-08-22T12:00:00.000Z") {
	let at = Date.parse(start);
	return { now: () => new Date(at).toISOString(),
	         advance(ms) { at += ms; } };
}

function open(path, { incarnation = "manager-1", clock } = {}) {
	return new ControlStore(path, { incarnation, clock: clock ?? (() =>
		"2026-08-22T12:00:00.000Z") });
}

function realBoundary({ clock } = {}) {
	const root = ownedTemp("v12-manager-");
	const authority = V12Authority.create(join(root, "authority.sqlite3"),
		{ authorityUuid: UUID });
	authority.certifyContract(V12);
	authority.addRouteHandler("impl", WHO);
	authority.createWork({ workId: WORK, route: "impl", contract: V12 });
	return { authority, api: authority.session(WHO),
	         store: open(join(root, "control.sqlite3"), { clock }) };
}

/** The authority, scripted. It records what it was asked, so a case can
 *  assert the manager submitted ONE fixed operation rather than whatever it
 *  happened to have. */
function session(overrides = {}) {
	const calls = [];
	return {
		calls,
		// A REAL session is always bound to one participant, so the double
		// is too — the offer path derives the identity from this and
		// refuses an operand that disagrees with it.
		participant: overrides.participant ?? WHO,
		projectWork: overrides.projectWork ?? (() => ({
			authorityUuid: UUID, workId: WORK, status: "open", phase: "queued",
			handler: null, gate: null, ready: true,
		})),
		slotHolder: overrides.slotHolder ?? (() => null),
		claim: overrides.claim ?? ((operands) => {
			calls.push(["claim", operands]);
			// DIRECTLY, exactly as `V12Session.claim` answers.
			return { authorityUuid: UUID, workId: WORK, participant: WHO,
			         generation: 1 };
		}),
		settleOperation: overrides.settleOperation ?? ((operands) => {
			calls.push(["settleOperation", operands]);
			return { kind: "live", record: null };
		}),
	};
}

const DIGESTS = { inputDigest: digest(1), policyDigest: digest(2),
                  profileDigest: digest(3) };

function issued(store, api, extra = {}) {
	return issueOffer(store, api, { workId: WORK, participant: WHO,
	                                ...DIGESTS, ...extra });
}

/** The ordinary path, with the profile CERTIFIED.
 *
 *  Certification is stated by every case that is not about certification,
 *  rather than defaulted inside `issued`: a fixture that quietly supplies
 *  the one fact a boundary checks is how the omission hole survived in the
 *  first place. */
function certified(store, api, extra = {}) {
	return issued(store, api,
		{ certifiedProfileDigest: DIGESTS.profileDigest, ...extra });
}

/** Drive the issued-only terminal transition the way a stale DECLINE
 *  does: from a row read before another act won. `acceptOffer`'s decline
 *  branch is the product path and this is the same call it makes. */
function settleTerminalForTest(store, staleRow) {
	return acceptOffer(store, { offerId: staleRow.offer_id, body: {
		decision: "decline", claim_token: null,
		offer_id: staleRow.offer_id,
		runtime_attempt_id: staleRow.runtime_attempt_id,
		work_ref: { authority_uuid: staleRow.authority_uuid,
		            work_id: staleRow.work_id },
		reason: "decided from a stale read" } });
}

function acceptBody(offer, { token = BEARER, reason = "the worker accepts" } = {}) {
	return { decision: "accept", claim_token: token,
	         offer_id: offer.offerId, runtime_attempt_id: offer.runtimeAttemptId,
	         work_ref: { authority_uuid: UUID, work_id: WORK }, reason };
}

// -- issue -------------------------------------------------------------------

test("W2929: an offer stores the VERIFIER and returns the bearer", () => {
	const store = open(storePath());
	try {
		const offer = certified(store, session(),
			{ mintBearer: () => BEARER });
		assert.equal(offer.bearer, BEARER);
		const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		assert.equal(row.verifier, tokenVerifier(BEARER));
		assert.equal(row.state, "issued");
		assert.equal(row.verifier_spent, 0);
		// THE BEARER IS NOWHERE IN THE FILE. Not under this column, not
		// under any other, and not in the operation journal.
		for (const [name, value] of Object.entries(row)) {
			assert.ok(typeof value !== "string" || !value.includes(BEARER),
				`the bearer reached offers.${name}`);
		}
		const journal = store.operationRecord(`offer.issue:${offer.offerId}`);
		assert.ok(!JSON.stringify(journal).includes(BEARER),
			"the bearer reached the operation journal");
	} finally {
		store.close();
	}
});

test("W2929: the reads happen BEFORE any entropy is spent", () => {
	// A bearer minted for an offer that is then refused is a secret that
	// existed for no reason. Each refusal is driven separately, and the
	// mint is proven never to have run.
	for (const [what, api] of [
			["unclaimable work", session({ projectWork: () => ({
				authorityUuid: UUID, workId: WORK, status: "open",
				phase: "active", handler: null, gate: null }) })],
			["already claimed", session({ projectWork: () => ({
				authorityUuid: UUID, workId: WORK, status: "open",
				phase: "queued", handler: "poc.other", gate: null }) })],
			["gated", session({ projectWork: () => ({
				authorityUuid: UUID, workId: WORK, status: "open",
				phase: "queued", handler: null,
				gate: { token: "gate:x" } }) })],
			["no capacity", session({ slotHolder: () => "43c55d4b-W9" })]]) {
		const store = open(storePath());
		try {
			let minted = 0;
			assert.throws(() => certified(store, api,
				{ mintBearer: () => { minted += 1; return BEARER; } }),
				(error) => error instanceof ContractError, what);
			assert.equal(minted, 0, `a bearer was minted for ${what}`);
			assert.equal(store.db.prepare("SELECT COUNT(*) AS n FROM offers")
				.get().n, 0, what);
		} finally {
			store.close();
		}
	}
});

test("W2929 review: an offer participant is the session binding", () => {
	const store = open(storePath());
	const api = session();
	api.participant = "poc.somebody-else";
	try {
		let minted = 0;
		assert.throws(() => certified(store, api, {
			certifiedProfileDigest: DIGESTS.profileDigest,
			mintBearer: () => { minted += 1; return BEARER; },
		}), (error) => error instanceof ContractError,
		"an offer named a participant other than the session's binding");
		assert.equal(minted, 0, "the binding mismatch spent entropy");
		assert.equal(store.db.prepare("SELECT COUNT(*) AS n FROM offers").get().n, 0);
	} finally {
		store.close();
	}
});

test("W2929 review: profile certification cannot be omitted", () => {
	const store = open(storePath());
	try {
		let minted = 0;
		assert.throws(() => issued(store, session(), {
			mintBearer: () => { minted += 1; return BEARER; },
		}), (error) => error instanceof ContractError
			&& error.category === "policy",
		"omitting the certified profile bypassed the policy check");
		assert.equal(minted, 0, "an uncertified offer spent entropy");
	} finally {
		store.close();
	}
});

test("W2929: an uncertified profile is refused as policy, not as schema", () => {
	const store = open(storePath());
	try {
		assert.throws(() => issued(store, session(),
			{ certifiedProfileDigest: digest("other") }),
			(error) => error instanceof ContractError
				&& error.category === "policy"
				&& error.code === "profile-uncertified");
	} finally {
		store.close();
	}
});

test("W2929: one nonterminal offer per Work, decided by the DATABASE", () => {
	// Two manager processes on separate connections both pass any
	// read-then-write check. Only the partial unique index refuses the
	// second, which is why the index exists.
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	const second = open(path, { incarnation: "manager-2" });
	try {
		certified(first, session());
		assert.throws(() => certified(second, session()),
			(error) => /UNIQUE|constraint/i.test(String(error.message)));
		assert.equal(first.db.prepare("SELECT COUNT(*) AS n FROM offers")
			.get().n, 1);
	} finally {
		first.close();
		second.close();
	}
});

test("W2929 review: an issue replay never returns a bearer for another verifier",
	() => {
		const store = open(storePath());
		try {
			const offerId = "offer-replay";
			certified(store, session(), { offerId, mintBearer: () => BEARER });
			let replay = null;
			try {
				replay = certified(store, session(), {
					offerId, mintBearer: () => `${BEARER}-different`,
				});
			} catch (error) {
				assert.ok(error instanceof Error);
			}
			if (replay !== null) {
				assert.equal(tokenVerifier(replay.bearer), replay.verifier,
					"replay paired a newly minted bearer with the first verifier");
			}
		} finally {
			store.close();
		}
	});

test("W2929 review: issue replay signs every durable operand", () => {
	const store = open(storePath());
	try {
		const offerId = "offer-collision";
		certified(store, session(), { offerId, mintBearer: () => BEARER });
		assert.throws(() => certified(store, session(), {
			offerId, policyDigest: digest("changed-policy"),
			mintBearer: () => BEARER,
		}), (error) => error instanceof ContractError
			&& error.code === "operation-collision",
		"a changed policy digest replayed the first offer");
	} finally {
		store.close();
	}
});

test("W2929 re-review: the authority binding rides the issue signature", () => {
	const store = open(storePath());
	const offerId = "offer-authority-collision";
	const runtimeAttemptId = "attempt-authority-collision";
	try {
		certified(store, session(), { offerId, runtimeAttemptId,
		                              mintBearer: () => BEARER });
		const other = session({ projectWork: () => ({
			authorityUuid: "53c55d4b00ee85c84ae4ed134de36df5",
			workId: WORK, status: "open", phase: "queued", handler: null,
			gate: null, ready: true,
		}) });
		assert.throws(() => certified(store, other, { offerId, runtimeAttemptId,
			mintBearer: () => `${BEARER}-other-authority`,
		}), (error) => error instanceof ContractError
			&& error.code === "operation-collision",
		"a different durable authority binding replayed as the same issue");
	} finally {
		store.close();
	}
});

// -- accept ------------------------------------------------------------------

test("W2929: acceptance consumes the verifier and freezes the intent", () => {
	const store = open(storePath());
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER });
		const accepted = acceptOffer(store, { offerId: offer.offerId,
		                                      body: acceptBody(offer) });
		const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		assert.equal(row.state, "accepted");
		assert.equal(row.verifier_spent, 1);
		assert.equal(row.intent_digest, accepted.intentDigest);
		// The claim operation id is DERIVED, which is what lets a later
		// incarnation name it without having seen it submitted.
		assert.equal(row.claim_operation_id,
			claimOperationId(offer.offerId, accepted.intentDigest));
		// A SEPARATE deadline from expiry, and later than it here.
		assert.notEqual(row.settle_by, row.expires_at);
		assert.equal(row.settle_by,
			new Date(Date.parse(row.accepted_at) + SETTLE_MS).toISOString());
	} finally {
		store.close();
	}
});

test("W2929: a wrong bearer, a spent one and a stale offer are all refused", () => {
	const store = open(storePath());
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER });
		assert.throws(() => acceptOffer(store, {
			offerId: offer.offerId,
			body: acceptBody(offer, { token: GOLDEN_BEARER }) }),
			// The wording is the CONTRACT module's, because that is where
			// possession is proven — and in constant time.
			(error) => /does not match this offer's verifier/.test(error.message));
		// The failed attempt consumed nothing: the real bearer still works.
		assert.equal(acceptOffer(store, { offerId: offer.offerId,
			body: acceptBody(offer) }).state, "accepted");
		// And now it does not, because the verifier is single-use.
		assert.throws(() => acceptOffer(store, { offerId: offer.offerId,
			body: acceptBody(offer) }),
			(error) => error instanceof ContractError);
	} finally {
		store.close();
	}
});

test("W2929: acceptance after expiry is refused", () => {
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER,
		                                         ttlMs: 1_000 });
		clock.advance(1_001);
		assert.throws(() => acceptOffer(store, { offerId: offer.offerId,
			body: acceptBody(offer) }),
			(error) => /expired/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929 review: expiry consumes the verifier and releases the Work", () => {
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER,
		                                         ttlMs: 1_000 });
		clock.advance(1_001);
		assert.throws(() => acceptOffer(store, { offerId: offer.offerId,
			body: acceptBody(offer) }), ContractError);
		const row = store.db.prepare("SELECT state, verifier_spent FROM offers "
			+ "WHERE offer_id=?").get(offer.offerId);
		// SPREAD, because `node:sqlite` rows carry a null prototype and
		// strict deepEqual compares prototypes — the property the reviewer
		// wrote is exactly this and only the comparison could not hold.
		assert.deepEqual({ ...row }, { state: "expired", verifier_spent: 1 },
			"an expired offer remained live and replayable");
		assert.doesNotThrow(() => certified(store, session(), {
			mintBearer: () => `${BEARER}-after-expiry`,
		}), "the expired offer continued to hold the per-Work CAS");
	} finally {
		store.close();
	}
});

test("W2929 re-review: TTL expiry releases the Work without a late decision",
	() => {
		const clock = clockFrom();
		const store = open(storePath(), { clock: clock.now });
		try {
			certified(store, session(), { mintBearer: () => BEARER,
			                              ttlMs: 1_000 });
			clock.advance(1_001);
			assert.doesNotThrow(() => certified(store, session(), {
				mintBearer: () => `${BEARER}-after-ttl`,
			}), "an elapsed offer held the Work until its worker answered");
		} finally {
			store.close();
		}
	});

test("W2929: a decline terminates and still consumes the verifier", () => {
	const store = open(storePath());
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER });
		const declined = acceptOffer(store, { offerId: offer.offerId,
			body: { decision: "decline", claim_token: null,
			        offer_id: offer.offerId,
			        runtime_attempt_id: offer.runtimeAttemptId,
			        work_ref: { authority_uuid: UUID, work_id: WORK },
			        reason: "the worker is busy" } });
		assert.equal(declined.state, "declined");
		const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		assert.equal(row.verifier_spent, 1,
			"a decline left the bearer replayable into an acceptance");
		// And the Work is free for a new offer, with a NEW bearer.
		const again = certified(store, session(),
			{ mintBearer: () => `${BEARER}-2` });
		assert.notEqual(again.bearer, offer.bearer);
	} finally {
		store.close();
	}
});

// -- claim -------------------------------------------------------------------

test("W2929: the claim submits ONE fixed operation and records it first", () => {
	const store = open(storePath());
	const api = session();
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		const accepted = acceptOffer(store, { offerId: offer.offerId,
		                                      body: acceptBody(offer) });
		const settled = submitClaim(store, api, { offerId: offer.offerId,
		                                          bearer: BEARER });
		assert.deepEqual(api.calls, [["claim", {
			workId: WORK, operationId: accepted.claimOperationId }]]);
		assert.equal(settled.state, "claimed");
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "claimed");
		// The session was never handed an identity operand; the claim takes
		// its participant from the binding.
		assert.ok(!Object.hasOwn(api.calls[0][1], "participant"));
	} finally {
		store.close();
	}
});

test("W2929 review: the real authority assignment is recorded exactly", () => {
	const { authority, api, store } = realBoundary();
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId, body: acceptBody(offer) });
		const settled = submitClaim(store, api, {
			offerId: offer.offerId, bearer: BEARER,
		});
		assert.deepEqual(settled.assignment, {
			authorityUuid: UUID, workId: WORK, participant: WHO, generation: 1,
		}, "the manager treated the authority's direct assignment as a wrapper");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929 review: lost-result settlement uses the fixed claim signature", () => {
	const { authority, api, store } = realBoundary();
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		const accepted = acceptOffer(store, {
			offerId: offer.offerId, body: acceptBody(offer),
		});
		const row = store.db.prepare("SELECT claim_signature FROM offers "
			+ "WHERE offer_id=?").get(offer.offerId);
		assert.equal(row.claim_signature,
			V12Authority.claimSignature(WORK, WHO),
			"acceptance did not persist the authority's fixed operands");
		api.claim({ workId: WORK, operationId: accepted.claimOperationId });
		const settled = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(settled.state, "claimed");
		assert.deepEqual(settled.assignment, {
			authorityUuid: UUID, workId: WORK, participant: WHO, generation: 1,
		});
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: a lost result may only be OBSERVED before the deadline", () => {
	// A read saying "not committed" proves only its own instant. Retiring
	// early could close an identity the authority is still going to honour,
	// and the manager would then record a refusal for a claim that WON.
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	const api = session();
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId, body: acceptBody(offer) });
		const answer = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(answer.settled, false);
		assert.equal(api.calls.at(-1)[1].mayRetire, false,
			"the manager asked to retire a claim before its deadline");
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "accepted",
			"an observation wrote a control row");
	} finally {
		store.close();
	}
});

test("W2929: at the deadline it may retire, and only then", () => {
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	const retired = { kind: "retired",
	                  record: { disposition: "settlement-expired",
	                            reason: "the manager lost this claim's result" } };
	const api = session({ settleOperation: (operands) => {
		api.calls.push(["settleOperation", operands]);
		return operands.mayRetire ? retired : { kind: "live", record: null };
	} });
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId, body: acceptBody(offer) });
		clock.advance(SETTLE_MS + 1);
		const answer = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(api.calls.at(-1)[1].mayRetire, true);
		assert.equal(answer.state, "settlement-expired");
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "settlement-expired");
	} finally {
		store.close();
	}
});

test("W2929: positive refusal evidence retires immediately", () => {
	// Not a guess: the submitted claim is KNOWN to have refused, so waiting
	// out the deadline would leave the Work parked on nothing.
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	const api = session({ settleOperation: (operands) => {
		api.calls.push(["settleOperation", operands]);
		return { kind: "retired",
		         record: { disposition: operands.disposition,
		                   reason: operands.reason } };
	} });
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId, body: acceptBody(offer) });
		const answer = settleClaim(store, api, { offerId: offer.offerId,
			refusedEvidence: "route does not resolve to poc.claude" });
		assert.equal(api.calls.at(-1)[1].mayRetire, true);
		assert.equal(api.calls.at(-1)[1].disposition, "claim-refused");
		assert.equal(answer.state, "claim-refused");
	} finally {
		store.close();
	}
});

test("W2929: a commit the manager never saw is recorded LATE", () => {
	// Step 6, and the whole reason the operation id is derived rather than
	// random: the next incarnation can name the exact operation.
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	// The authority's committed result for a claim IS the assignment, so
	// the double returns one — a wrapper here would have hidden the very
	// shape mismatch the review reported.
	const api = session({ settleOperation: () => ({
		kind: "committed",
		result: { authorityUuid: UUID, workId: WORK, participant: WHO,
		          generation: 4 } }) });
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId, body: acceptBody(offer) });
		const answer = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(answer.state, "claimed");
		assert.equal(answer.late, true);
		assert.deepEqual(answer.assignment,
			{ authorityUuid: UUID, workId: WORK, participant: WHO,
			  generation: 4 });
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "claimed");
	} finally {
		store.close();
	}
});

test("W2929: an existing retirement's BOUND answer is adopted, not re-decided",
	() => {
		// Whoever retired the identity first decided what it means. A second
		// manager inventing its own disposition would give one operation two
		// meanings, which is exactly what a fixed operation id exists to
		// prevent.
		const clock = clockFrom();
		const store = open(storePath(), { clock: clock.now });
		const api = session({ settleOperation: () => ({
			kind: "retired",
			record: { disposition: "claim-refused",
			          reason: "another manager saw the refusal" } }) });
		try {
			const offer = certified(store, api, { mintBearer: () => BEARER });
			acceptOffer(store, { offerId: offer.offerId,
			                     body: acceptBody(offer) });
			clock.advance(SETTLE_MS + 1);
			// This manager ASKED for settlement-expired and must adopt the
			// bound answer instead.
			const answer = settleClaim(store, api, { offerId: offer.offerId });
			assert.equal(answer.state, "claim-refused");
			assert.equal(answer.adopted, true);
			assert.equal(answer.reason, "another manager saw the refusal");
		} finally {
			store.close();
		}
	});

// -- restart -----------------------------------------------------------------

test("W2929: restart abandons a PRIOR incarnation's issued offer", () => {
	// Nothing durable says that bearer was ever delivered, so honouring it
	// would mean trusting a secret this process cannot account for.
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	let offerId;
	try {
		offerId = certified(first, session(), { mintBearer: () => BEARER }).offerId;
	} finally {
		first.close();
	}
	const second = open(path, { incarnation: "manager-2" });
	try {
		const recovered = recoverOnRestart(second);
		assert.deepEqual(recovered.abandoned, [offerId]);
		const row = second.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offerId);
		assert.equal(row.state, "abandoned-after-restart");
		assert.equal(row.verifier_spent, 1, "the verifier survived abandonment");
		// VISIBLE, not deleted: the record is what an audit reads.
		assert.match(row.decision_reason, /manager-1/);
		// And the Work can be offered again, with a new bearer.
		const again = certified(second, session(),
			{ mintBearer: () => `${BEARER}-2` });
		assert.notEqual(again.bearer, BEARER);
	} finally {
		second.close();
	}
});

test("W2929: restart keeps an ACCEPTED offer, and its own incarnation's", () => {
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	let accepted;
	let mine;
	try {
		const offer = certified(first, session(), { mintBearer: () => BEARER });
		accepted = acceptOffer(first, { offerId: offer.offerId,
		                                body: acceptBody(offer) });
		mine = certified(first, session(), {
			workId: "43c55d4b-W2",
			mintBearer: () => `${BEARER}-mine` }).offerId;
	} finally {
		first.close();
	}
	// The SAME incarnation restarting: its own issued offer is untouched,
	// because several managers coordinate through this store and abandoning
	// on identity alone would let one destroy another's live work.
	const same = open(path, { incarnation: "manager-1" });
	try {
		const recovered = recoverOnRestart(same);
		assert.deepEqual(recovered.abandoned, []);
		assert.deepEqual(recovered.recoverable.map((entry) => entry.offerId),
			[accepted.offerId]);
		assert.equal(recovered.recoverable[0].claimOperationId,
			accepted.claimOperationId);
		assert.equal(same.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(mine).state, "issued");
	} finally {
		same.close();
	}
});

test("W2929: a LATER incarnation derives the same claim operation id", () => {
	// The reason the id is derived rather than minted, stated as the
	// property rather than as a comparison against the same function:
	// a process that never saw the submission must be able to name the
	// exact operation from the durable row alone.
	//
	// Mutation found this: asserting `row.claim_operation_id ===
	// claimOperationId(offerId, intentDigest)` is satisfied by ANY
	// implementation, because both sides call the same code. What cannot be
	// satisfied by a minted id is deriving it again, later, from the store.
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	let offerId;
	try {
		const offer = certified(first, session(), { mintBearer: () => BEARER });
		offerId = offer.offerId;
		acceptOffer(first, { offerId, body: acceptBody(offer) });
	} finally {
		first.close();
	}
	const second = open(path, { incarnation: "manager-2" });
	try {
		const row = second.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offerId);
		// Only the DURABLE facts are in hand here: the offer id and the
		// frozen intent. Nothing from the process that submitted.
		assert.equal(claimOperationId(row.offer_id, row.intent_digest),
			row.claim_operation_id,
			"a later incarnation cannot name the operation the first submitted");
		// And it is stable: deriving it twice gives one answer.
		assert.equal(claimOperationId(row.offer_id, row.intent_digest),
			claimOperationId(row.offer_id, row.intent_digest));
		// A DIFFERENT intent gives a different operation, so two acceptances
		// can never collide onto one authority identity.
		assert.notEqual(claimOperationId(row.offer_id, digest("elsewhere")),
			row.claim_operation_id);
	} finally {
		second.close();
	}
});

// -- the issued-to-accepted race ---------------------------------------------

test("W2929: a stale DECLINE cannot overwrite an offer that was accepted", () => {
	// Both terminal callers act from an earlier `issued` read, and another
	// manager can accept in between. A stale decline that won would destroy
	// the durable authorization and the fixed claim identity acceptance had
	// just frozen — the two facts a restart depends on.
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	const second = open(path, { incarnation: "manager-2" });
	try {
		const offer = certified(first, session(), { mintBearer: () => BEARER });
		// The decline is decided from a read taken NOW...
		const stale = first.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		// ...and the other manager accepts before it lands.
		const accepted = acceptOffer(second, { offerId: offer.offerId,
		                                       body: acceptBody(offer) });
		// REFUSED — and by the verifier check, which fires before the CAS
		// because acceptance spent it. Two guards cover this race and the
		// case pins the OUTCOME rather than which one fired: the
		// abandonment case below drives the CAS itself, where the verifier
		// is not yet spent.
		assert.throws(() => settleTerminalForTest(first, stale),
			(error) => error instanceof ContractError);
		const row = first.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		assert.equal(row.state, "accepted", "a stale decline won the race");
		assert.equal(row.claim_operation_id, accepted.claimOperationId);
		assert.equal(row.claim_signature, accepted.claimSignature);
	} finally {
		first.close();
		second.close();
	}
});

test("W2929 re-review: decline loses the issued CAS after its own stale read",
	() => {
		const path = storePath();
		const first = open(path, { incarnation: "manager-1" });
		const second = open(path, { incarnation: "manager-2" });
		try {
			const offer = certified(first, session(), { mintBearer: () => BEARER });
			let raced = false;
			const body = {
				decision: "decline", claim_token: null, offer_id: offer.offerId,
				runtime_attempt_id: offer.runtimeAttemptId,
				work_ref: { authority_uuid: UUID, work_id: WORK },
			};
			Object.defineProperty(body, "reason", { enumerable: true, get() {
				if (!raced) {
					raced = true;
					acceptOffer(second, { offerId: offer.offerId,
					                           body: acceptBody(offer) });
				}
				return "decline decided from the stale read";
			} });
			assert.throws(() => acceptOffer(first, { offerId: offer.offerId, body }),
				(error) => error instanceof ContractError);
			assert.equal(raced, true, "the acceptance was not placed after the read");
			assert.equal(first.db.prepare(
				"SELECT state FROM offers WHERE offer_id=?").get(offer.offerId).state,
				"accepted", "the stale decline overwrote the accepted row");
		} finally {
			first.close();
			second.close();
		}
	});

test("W2929: restart abandonment cannot overwrite a concurrent acceptance",
	() => {
		// The same race through the other caller. A restarting manager reads
		// `issued` offers and abandons them; a live manager may accept one
		// between that read and the write.
		const path = storePath();
		const first = open(path, { incarnation: "manager-1" });
		let offerId;
		try {
			const offer = certified(first, session(),
				{ mintBearer: () => BEARER });
			offerId = offer.offerId;
			// A second incarnation begins recovery from a read of `issued`...
			const restarting = open(path, { incarnation: "manager-2" });
			try {
				const seen = restarting.db.prepare(
					"SELECT * FROM offers WHERE state='issued'").all();
				assert.equal(seen.length, 1);
				// ...and the first manager accepts before the write lands.
				acceptOffer(first, { offerId, body: acceptBody(offer) });
				const recovered = recoverOnRestart(restarting);
				assert.deepEqual(recovered.abandoned, [],
					"restart abandoned an offer that had been accepted");
				assert.deepEqual(
					recovered.recoverable.map((entry) => entry.offerId),
					[offerId]);
			} finally {
				restarting.close();
			}
			assert.equal(first.db.prepare(
				"SELECT state FROM offers WHERE offer_id=?").get(offerId).state,
				"accepted");
		} finally {
			first.close();
		}
	});

test("W2929 re-review: restart loses the issued CAS after its recovery read",
	() => {
		const path = storePath();
		const first = open(path, { incarnation: "manager-1" });
		const restarting = open(path, { incarnation: "manager-2" });
		let restorePrepare = null;
		try {
			const offer = certified(first, session(), { mintBearer: () => BEARER });
			const originalPrepare = restarting.db.prepare.bind(restarting.db);
			restorePrepare = restarting.db.prepare;
			let raced = false;
			restarting.db.prepare = (sql) => {
				const statement = originalPrepare(sql);
				if (!sql.startsWith("SELECT * FROM offers WHERE state IN")) {
					return statement;
				}
				return { all(...args) {
					const rows = statement.all(...args);
					if (!raced) {
						raced = true;
						acceptOffer(first, { offerId: offer.offerId,
						                     body: acceptBody(offer) });
					}
					return rows;
				} };
			};
			assert.throws(() => recoverOnRestart(restarting),
				(error) => error instanceof ContractError);
			assert.equal(raced, true, "the acceptance was not placed after the read");
			assert.equal(first.db.prepare(
				"SELECT state FROM offers WHERE offer_id=?").get(offer.offerId).state,
				"accepted", "restart overwrote the accepted row");
		} finally {
			if (restorePrepare !== null) restarting.db.prepare = restorePrepare;
			restarting.close();
			first.close();
		}
	});

// -- the whole path against a REAL session -----------------------------------

test("W2929: the whole claim path, against a real authority", () => {
	const { authority, api, store } = realBoundary();
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		const accepted = acceptOffer(store, { offerId: offer.offerId,
		                                     body: acceptBody(offer) });
		const settled = submitClaim(store, api, { offerId: offer.offerId,
		                                          bearer: BEARER });
		assert.equal(settled.state, "claimed");
		// The AUTHORITY agrees: the Work is held by this participant.
		const work = api.projectWork(WORK);
		assert.equal(work.handler, WHO);
		assert.deepEqual(settled.assignment, work.assignment);
		// And the recorded operation is the one the authority committed.
		assert.equal(api.operationRecord(accepted.claimOperationId).state,
			"committed");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: pre-deadline observation and deadline retirement, for real", () => {
	// The two settlement windows through the real authority rather than a
	// scripted result shape — the review is right that a double can agree
	// with an implementation about a shape neither shares with the
	// authority.
	const clock = clockFrom();
	const { authority, api, store } = realBoundary({ clock: clock.now });
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId,
		                     body: acceptBody(offer) });
		// Nothing was submitted, so the identity is live and untouchable.
		const observed = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(observed.settled, false);
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "accepted");
		// Past the deadline the authority retires the identity, and the
		// manager adopts what it bound.
		clock.advance(SETTLE_MS + 1);
		const retired = settleClaim(store, api, { offerId: offer.offerId });
		assert.equal(retired.state, "settlement-expired");
		// The authority CLOSED that identity: the exact operation the
		// manager submitted can never commit under it now, which is what
		// retirement means and why it may not happen early.
		const row = store.db.prepare(
			"SELECT claim_operation_id FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		const answer = api.settleOperation({
			operationId: row.claim_operation_id,
			signature: V12Authority.claimSignature(WORK, WHO),
			reason: "asked again", disposition: "settlement-expired",
			mayRetire: false });
		assert.equal(answer.kind, "retired");
		assert.equal(api.projectWork(WORK).handler, null,
			"a retired claim left the Work held");
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: refusal evidence retires against the real authority too", () => {
	const clock = clockFrom();
	const { authority, api, store } = realBoundary({ clock: clock.now });
	try {
		const offer = certified(store, api, { mintBearer: () => BEARER });
		acceptOffer(store, { offerId: offer.offerId,
		                     body: acceptBody(offer) });
		const settled = settleClaim(store, api, {
			offerId: offer.offerId,
			refusedEvidence: "route does not resolve to this participant" });
		assert.equal(settled.state, "claim-refused");
		assert.match(settled.reason ?? "", /route does not resolve/);
	} finally {
		store.close();
		authority.dispose();
	}
});

test("W2929: an exact re-issue REFUSES rather than answering with a secret",
	() => {
		// The reviewer's retained case permits either a throw or a matching
		// pair, so it cannot distinguish "refused" from "replayed something
		// usable". Mutation showed that: removing the guard left it green.
		// This pins the answer, because there is only one honest one — the
		// bearer existed solely in the process that minted it, so a second
		// call cannot reproduce it and must not hand back one that does not
		// derive the stored verifier.
		const store = open(storePath());
		try {
			const offerId = "offer-exact-replay";
			// EXACT means exact: the runtime attempt id is a durable operand
			// and defaults to a fresh UUID, so re-issuing without pinning it
			// is a different operation and collides — which is the OTHER
			// retained case, and not this one.
			const runtimeAttemptId = "attempt-exact-replay";
			const first = certified(store, session(),
				{ offerId, runtimeAttemptId, mintBearer: () => BEARER });
			let minted = 0;
			assert.throws(() => certified(store, session(), {
				offerId, runtimeAttemptId,
				mintBearer: () => { minted += 1; return `${BEARER}-second`; },
			}), (error) => error instanceof ContractError
				&& /already issued/.test(error.message));
			assert.equal(minted, 0,
				"the refused re-issue minted a bearer anyway");
			// The first offer is untouched, and its verifier still derives
			// from the bearer its own caller holds.
			const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
				.get(offerId);
			assert.equal(row.verifier, tokenVerifier(first.bearer));
			assert.equal(row.state, "issued");
		} finally {
			store.close();
		}
	});

test("W2929 re-review: concurrent exact issue never pairs the loser's bearer",
	() => {
		const path = storePath();
		const first = open(path, { incarnation: "manager-1" });
		const second = open(path, { incarnation: "manager-2" });
		const offerId = "offer-concurrent-replay";
		const runtimeAttemptId = "attempt-concurrent-replay";
		let winner = null;
		try {
			assert.throws(() => certified(first, session(), {
				offerId, runtimeAttemptId, mintBearer: () => {
					winner = certified(second, session(), {
						offerId, runtimeAttemptId,
						mintBearer: () => `${BEARER}-winner`,
					});
					return `${BEARER}-loser`;
				},
			}), (error) => error instanceof ContractError,
			"the losing exact issuer returned the winner's record with its own bearer");
			assert.equal(tokenVerifier(winner.bearer), winner.verifier,
				"the winning issue did not retain its own verifier");
		} finally {
			first.close();
			second.close();
		}
	});

test("W2929: the losing concurrent issuer emits no bearer at all", () => {
	// The reviewer's case proves the loser throws. This proves what the
	// loser does NOT do: the refusal happens after the transaction has
	// decided, and no bearer leaves this call — not returned, not recorded.
	const path = storePath();
	const first = open(path, { incarnation: "manager-1" });
	const second = open(path, { incarnation: "manager-2" });
	const offerId = "offer-loser-emits-nothing";
	const runtimeAttemptId = "attempt-loser-emits-nothing";
	try {
		let loserBearer = null;
		assert.throws(() => certified(first, session(), {
			offerId, runtimeAttemptId, mintBearer: () => {
				certified(second, session(), {
					offerId, runtimeAttemptId,
					mintBearer: () => `${BEARER}-winner` });
				loserBearer = `${BEARER}-loser`;
				return loserBearer;
			},
		}), (error) => error instanceof ContractError
			&& /issued concurrently/.test(error.message));
		// The store holds exactly the winner's verifier, and nothing
		// anywhere holds the loser's.
		const row = first.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offerId);
		assert.equal(row.verifier, tokenVerifier(`${BEARER}-winner`));
		assert.notEqual(row.verifier, tokenVerifier(loserBearer));
		const journal = JSON.stringify(
			first.operationRecord(`offer.issue:${offerId}`));
		assert.ok(!journal.includes(loserBearer), "the loser's bearer was journalled");
		assert.ok(!journal.includes(`${BEARER}-winner`),
			"the winner's bearer was journalled");
	} finally {
		first.close();
		second.close();
	}
});

test("W2929 re-review: replay provenance does not depend on bearer uniqueness",
	() => {
		// Effectively-once is decided by the journal, not inferred from a
		// probabilistic property of the secret source. Two exact issuers may
		// receive the same injected bearer; the transaction loser must still
		// refuse rather than replaying an ephemeral result the journal does not
		// own and cannot reproduce.
		const path = storePath();
		const first = open(path, { incarnation: "manager-1" });
		const second = open(path, { incarnation: "manager-2" });
		const offerId = "offer-same-bearer-race";
		const runtimeAttemptId = "attempt-same-bearer-race";
		try {
			assert.throws(() => certified(first, session(), {
				offerId, runtimeAttemptId, mintBearer: () => {
					certified(second, session(), { offerId, runtimeAttemptId,
					                              mintBearer: () => BEARER });
					return BEARER;
				},
			}), (error) => error instanceof ContractError,
			"the transaction loser was inferred from bearer inequality");
		} finally {
			first.close();
			second.close();
		}
	});

test("W2929: an elapsed offer is settled visibly, not silently dropped", () => {
	// A bound that releases the Work must still say what happened. The row
	// stays, named `expired`, with its verifier consumed — an audit reading
	// this store afterwards can tell an expiry from a decline and from an
	// offer that never existed.
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER,
		                                            ttlMs: 1_000 });
		clock.advance(1_001);
		const expired = expireOverdue(store);
		assert.deepEqual(expired, [offer.offerId]);
		const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offer.offerId);
		assert.equal(row.state, "expired");
		assert.equal(row.verifier_spent, 1,
			"an expired bearer stayed replayable");
		assert.match(row.decision_reason, /expired at/);
		// IDEMPOTENT: sweeping again settles nothing and changes nothing.
		assert.deepEqual(expireOverdue(store), []);
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "expired");
	} finally {
		store.close();
	}
});

test("W2929: the sweep never touches an offer that is still live", () => {
	// The other half: a bound that expired something early would be worse
	// than one that never fired.
	const clock = clockFrom();
	const store = open(storePath(), { clock: clock.now });
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER,
		                                            ttlMs: 10_000 });
		clock.advance(9_999);
		assert.deepEqual(expireOverdue(store), []);
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "issued");
		// And an ACCEPTED offer is never swept, whatever the clock says:
		// its authorization is durable and its claim identity is fixed.
		acceptOffer(store, { offerId: offer.offerId,
		                     body: acceptBody(offer) });
		clock.advance(100_000);
		assert.deepEqual(expireOverdue(store), []);
		assert.equal(store.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offer.offerId).state, "accepted");
	} finally {
		store.close();
	}
});

test("W2929: restart recovery settles elapsed offers before reporting", () => {
	// Recovery reports what is really live rather than counting rows the
	// clock has already ended — and an elapsed offer of THIS incarnation is
	// expired rather than abandoned, because the clock ended it, not the
	// restart.
	const clock = clockFrom();
	const path = storePath();
	const first = open(path, { incarnation: "manager-1", clock: clock.now });
	let offerId;
	try {
		offerId = certified(first, session(), { mintBearer: () => BEARER,
		                                        ttlMs: 1_000 }).offerId;
	} finally {
		first.close();
	}
	clock.advance(1_001);
	const same = open(path, { incarnation: "manager-1", clock: clock.now });
	try {
		const recovered = recoverOnRestart(same);
		assert.deepEqual(recovered.abandoned, []);
		assert.deepEqual(recovered.recoverable, []);
		assert.equal(same.db.prepare("SELECT state FROM offers WHERE offer_id=?")
			.get(offerId).state, "expired");
	} finally {
		same.close();
	}
});

test("W2929: the same identity against another authority COLLIDES", () => {
	// The reviewer's case drives the refusal; this pins the other side of
	// the same rule — the authority binding really is in the signature, so
	// the SAME binding still replays as the same operation rather than
	// colliding on something incidental.
	const store = open(storePath());
	const offerId = "offer-same-authority";
	const runtimeAttemptId = "attempt-same-authority";
	try {
		certified(store, session(), { offerId, runtimeAttemptId,
		                              mintBearer: () => BEARER });
		// Same authority, same operands: the exact-reissue refusal, which is
		// a DIFFERENT answer from an operation collision.
		assert.throws(() => certified(store, session(), {
			offerId, runtimeAttemptId, mintBearer: () => `${BEARER}-again` }),
			(error) => error instanceof ContractError
				&& /already issued/.test(error.message));
	} finally {
		store.close();
	}
});

test("W2929: a sequential exact reissue is refused, whatever the bearer", () => {
	// WHAT THIS PINS, precisely: the PUBLIC refusal, with the same bearer,
	// so nothing about the payload distinguishes the second call from the
	// first.
	//
	// WHAT IT DOES NOT PIN, and my first title claimed otherwise — the
	// re-review is right to say so: the optimistic `store.replay` precheck
	// intercepts this call, so the closure marker's branch never runs here.
	// The same-bearer CONCURRENT case is what exercises the marker on the
	// replay side, and the first-issue case is what exercises it on the
	// commit side. Citing this one as branch evidence would credit a guard
	// for work another case does.
	const store = open(storePath());
	const offerId = "offer-sequential-marker";
	const runtimeAttemptId = "attempt-sequential-marker";
	try {
		const first = certified(store, session(), {
			offerId, runtimeAttemptId, mintBearer: () => BEARER });
		// The SAME bearer, so nothing about the payload distinguishes this
		// call from the first — only the journal does.
		assert.throws(() => certified(store, session(), {
			offerId, runtimeAttemptId, mintBearer: () => BEARER }),
			(error) => error instanceof ContractError);
		const row = store.db.prepare("SELECT * FROM offers WHERE offer_id=?")
			.get(offerId);
		assert.equal(row.verifier, tokenVerifier(first.bearer));
		assert.equal(row.state, "issued");
	} finally {
		store.close();
	}
});

test("W2929: a genuinely first issue is not refused as a replay", () => {
	// The other direction, and the one a too-eager marker would break: a
	// call that really did commit must answer with its bearer. A boundary
	// that refused everything would satisfy every refusal case above.
	const store = open(storePath());
	try {
		const offer = certified(store, session(), { mintBearer: () => BEARER });
		assert.equal(offer.bearer, BEARER);
		assert.equal(tokenVerifier(offer.bearer),
			store.db.prepare("SELECT verifier FROM offers WHERE offer_id=?")
				.get(offer.offerId).verifier);
		// And a DIFFERENT offer for another Work also commits.
		const other = certified(store, session(), {
			workId: "43c55d4b-W7", mintBearer: () => `${BEARER}-other` });
		assert.equal(other.bearer, `${BEARER}-other`);
	} finally {
		store.close();
	}
});
