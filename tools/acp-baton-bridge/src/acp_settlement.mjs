// W55705 — the ACP participant's post-turn canonical claim settlement.
//
// `work/records/2026/08/finding-acp-turn-teardown-strands-live-worker/`.
//
// THE INCIDENT. `baton.claude` claimed W51487, launched a retained dogfood
// attempt, and the ACP delivery then ended normally. `runBridge` proved the
// agent process domain gone, published `idle`, and marked the offer presented.
// Canonical state still recorded the Work `active` with that participant at
// that episode; the runtime projection said the participant was free; the
// delegated container was still running with no supervising turn. Three facts,
// all published, none of them agreeing — and no incident, so nothing said the
// state needed a human.
//
// WHY THE ACP PATH NEEDS THIS WHEN THE CODEX PATH ALREADY HAS IT. The sibling
// dispatcher settles on a terminal `turn/completed` status, which is a
// SEMANTIC answer: the app-server says whether the model finished. ACP gives
// no such thing. A returned `promptText` is a TRANSPORT fact — the model
// stopped talking — and it is equally consistent with a claim passed back, a
// claim still held, and a process killed mid-attempt. So the reconciliation
// here runs after EVERY ACP turn outcome, the ordinary successful return
// included, rather than only after a caught error.
//
// WHAT IT DELIBERATELY DOES NOT DO, and each is a boundary the finding draws:
//
//   NOT A RELEASE. A surviving claim may hold real work. Releasing it
//   automatically would discard exactly what the fence exists to preserve, and
//   the ruling requires an explicit, generation-fenced operator act instead.
//   NOT A RUNTIME KILL. The delegated container is not in the ACP process
//   domain — run7 is the direct evidence, the domain ended while
//   `python3 /opt/baton/dogfood_entry.py` kept running — and W55758 owns that
//   recovery. This module reports a locator only when a trusted deployment
//   integration supplies one, and never scrapes prose, argv or logs for it.
//   NOT AN ACCEPTANCE. No partial output becomes a result here.
//   NOT A REPLACEMENT FOR THE PROCESS-DOMAIN FENCE. W28681's teardown fence is
//   stronger and separate: proving the domain gone does not settle the claim,
//   and settling the claim does not prove the domain gone. Neither clears the
//   other.
//
// THE STORE IS THE SIBLING'S. `QuarantineStore` was already made generic for
// exactly this second fence, and reusing it keeps one implementation of the
// rule that a DAMAGED marker is not an ABSENT one. A second persistence format
// would be a second place for that rule to be subtly wrong.

import { QuarantineStore, quarantineKey }
	from "../../codex-event-bridge/src/quarantine_store.mjs";

// The marker's key. The fence belongs to the canonical PARTICIPANT CLAIM SLOT
// — the thing that is actually stuck — and not to the short-lived agent
// process or its replaceable ACP session, either of which a restart legitimately
// changes while the claim survives untouched. The second component is a
// constant rather than a session id for that reason: it exists only because the
// shared key helper takes two.
const CLAIM_SLOT = "acp-claim";

// How long a fenced bridge waits between canonical re-reads. Bounded so a
// released claim is noticed without an operator restarting anything, and slow
// enough that a fence is not a polling loop against the authority.
export const RECONCILE_MS = 60_000;

/** One canonical `wait timeout=0` read, classified.
 *
 *  `claimed` — the participant still holds the EXACT delivered assignment.
 *  `secondary` — that exact assignment is gone but the participant holds a
 *  different claim, which occupies the same one slot. `held` — a claim is
 *  provably held but the delivery carried no Work to correlate it with, so the
 *  weaker word is used rather than inventing an attribution. `released` — no
 *  claim at all, so nothing was orphaned. `unreadable` — the read failed or
 *  the projection was malformed, which FAILS CLOSED, because "I could not ask"
 *  and "the answer was no" are different facts and only one of them justifies
 *  publishing `idle`.
 *
 *  Matched on the STRUCTURED work and episode the action carries, never by
 *  taking the opaque action key apart.
 */
export function classifySlot(payload, action) {
	const live = payload?.result?.actionable;
	if (!Array.isArray(live)) return { state: "unreadable" };
	const authority = typeof payload?.authority_uuid === "string"
		? payload.authority_uuid : null;
	const held = live.filter((entry) => entry?.kind === "work"
		&& entry.claimed === true
		&& Number.isSafeInteger(entry.episode_seq));
	const wanted = action?.work ?? null;
	const episode = Number.isSafeInteger(action?.episode_seq)
		? action.episode_seq : null;
	const exact = wanted
		? held.find((entry) => entry.work === wanted
			&& (episode === null || entry.episode_seq === episode))
		: null;
	if (exact) {
		return { state: "claimed", authority, work: exact.work,
			episode: exact.episode_seq, actionKey: exact.action_key };
	}
	if (held.length > 0) {
		const current = held[0];
		return { state: wanted ? "secondary" : "held", authority,
			work: current.work, episode: current.episode_seq,
			actionKey: current.action_key };
	}
	return { state: "released", authority };
}

export class AcpSettlement {
	/** `readSlot` is the canonical read, injected so a focused case pins the
	 *  exact argv rather than reaching a real authority. `runtime` is the same
	 *  publisher the bridge already holds: the incident row already carries
	 *  Work, episode, action key and session, is already owed to the runner's
	 *  CONFIGURED action owner, and already survives `idle` and restart until
	 *  that owner dismisses it, so inventing a second incident system here
	 *  would be a second thing to keep true.
	 */
	constructor(config, { runtime, logger = console, readSlot,
	                      store = null, now = () => Date.now() } = {}) {
		this.config = config;
		this.participant = config.baton.participant;
		this.runtime = runtime;
		// A LOGGER MISSING A LEVEL MUST NOT TAKE DOWN THE FENCE. The ACP
		// suite's own quiet helper carries `info` and `warn` only, and a
		// deployment is free to supply the same. Losing a claim settlement to
		// a logging shape mismatch would be an absurd way to reopen this
		// Work's incident, so the level degrades instead of throwing.
		this.logger = {
			info: (...args) => logger.info?.(...args),
			warn: (...args) => (logger.warn ?? logger.info)?.(...args),
			error: (...args) =>
				(logger.error ?? logger.warn ?? logger.info)?.(...args),
		};
		this.readSlot = readSlot;
		this.now = now;
		this.store = store ?? new QuarantineStore(
			config.stateDir, logger,
			{ suffix: ".acp-settlement.json", label: "ACP claim settlement" });
		this.fence = null;
		this.filing = null;
	}

	/** Whether readiness must be RETAINED — a strictly narrower question than
	 *  whether a claim survived.
	 *
	 *  W11910 ALREADY OWNS THE RECOVERABLE CASE, and this Work must not undo
	 *  it. A Work the participant still holds is re-offered by the authority as
	 *  that participant's own recovery action, and
	 *  `test("a claimed-Work recovery prompt that FAILED is delivered again")`
	 *  exists because suppressing that offer left a live claim with no wake and
	 *  no retry until somebody restarted the process — the exact
	 *  restart-dependent stall W11910 removed. Retaining readiness on an
	 *  `exact` claim would reintroduce it.
	 *
	 *  So the two corrections divide by whether ANYBODY WILL BE WOKEN:
	 *
	 *    claimed     the authority is still offering this Work to this
	 *                participant, so re-delivery IS the recovery. `idle` is
	 *                still wrong and an incident is still owed, but readiness
	 *                is not retained.
	 *    secondary   the delivered assignment is gone and a different claim
	 *    held        occupies the one slot, so this offer cannot be claimed and
	 *                spending a turn on it would prove only that.
	 *    unreadable  nothing is known, which fails closed.
	 *
	 *  Reported to the reviewer as a REFINEMENT of this record's acceptance
	 *  rather than applied silently: the finding says to retain later readiness
	 *  on any surviving claim, and that sentence and W11910 cannot both be
	 *  satisfied as written.
	 */
	fenced() {
		const fence = this.fence;
		if (fence === null) return false;
		// W55705 review (2026-09-01T03:41:20Z) [P1]: AN UNCOMMITTED MARKER IS
		// AN IN-PROCESS FENCE ONLY. `store.save` answers false precisely so a
		// caller can tell the two apart, and a lane that looks fenced here
		// while a restart would find nothing is the fail-open case this whole
		// module exists to remove. So it strands until the marker commits.
		if (fence.durable === false) return true;
		// W55705 review [P1]: A RESTORED MARKER HAS NOT MET THIS PROCESS'S
		// AUTHORITY YET. `restore()` believes the file, which is right — but
		// a dispatcher restarted against a DIFFERENT authority would then
		// deliver on the strength of a fence taken somewhere else. Nothing
		// is delivered until one canonical read has compared them.
		if (fence.verified !== true) return true;
		return fence.correlation !== "claimed";
	}

	/** Whether a claim survived at all, recoverable or not. */
	settled() { return this.fence !== null; }

	#key() { return quarantineKey(this.participant, CLAIM_SLOT); }

	#record(fence) {
		return { since: fence.since, participant: this.participant,
			authority: fence.authority ?? null, work: fence.work ?? null,
			episode: Number.isSafeInteger(fence.episode) ? fence.episode : null,
			actionKey: fence.actionKey ?? null,
			correlation: fence.correlation,
			offered: fence.offered ?? null,
			runtimeLocator: fence.runtimeLocator ?? null,
			incidentFiled: fence.incidentFiled === true,
			remedy: fence.remedy };
	}

	/** Restore a marker left by an earlier process, BEFORE the first wait or
	 *  the first `idle`.
	 *
	 *  A DAMAGED MARKER STAYS FENCED. A file at this exact key is positive
	 *  evidence that a previous process observed a surviving claim; losing its
	 *  payload destroys what it said, not what it meant. Reading corruption as
	 *  a clean slot would deliver into a lane that still cannot claim, which is
	 *  the failure the fence exists to prevent.
	 */
	restore() {
		const found = this.store.load(this.participant, CLAIM_SLOT);
		if (found.state === "absent") return { state: "absent" };
		if (found.state === "damaged") {
			const kept = this.store.preserveDamaged(this.participant, CLAIM_SLOT);
			this.fence = { since: this.now(), authority: null, work: null,
				episode: null, actionKey: null, correlation: "unreadable",
				offered: { work: null, episode: null, actionKey: null },
				incidentFiled: false, durable: true, restored: true,
				verified: false,
				checkedAt: 0, runtimeLocator: null,
				remedy: this.#remedy(null, null) };
			this.logger.error(
				`the ACP claim settlement marker for ${this.participant} is `
				+ `damaged (${found.reason}); the delivery lane stays fenced `
				+ `and the marker was preserved`
				+ (kept ? ` at ${kept}` : "") + `. A damaged fence is not an `
				+ `absent one: read the participant's canonical claim before `
				+ `clearing it.`);
			return { state: "damaged" };
		}
		const record = found.record;
		this.fence = { since: record.since, authority: record.authority ?? null,
			work: record.work ?? null, episode: record.episode ?? null,
			actionKey: record.actionKey ?? null,
			correlation: record.correlation ?? "unreadable",
			offered: record.offered ?? { work: record.work ?? null,
				episode: record.episode ?? null,
				actionKey: record.actionKey ?? null },
			runtimeLocator: record.runtimeLocator ?? null,
			incidentFiled: record.incidentFiled === true,
			durable: true, restored: true, verified: false, checkedAt: 0,
			remedy: record.remedy ?? this.#remedy(record.work, record.episode) };
		this.logger.warn(
			`restored an ACP claim settlement fence for ${this.participant}`
			+ (record.work ? ` on ${record.work}` : "")
			+ (Number.isSafeInteger(record.episode)
				? ` at assignment episode ${record.episode}` : "")
			+ `; no turn is delivered and no idle is published until a `
			+ `canonical read proves the claim released.`);
		return { state: "present" };
	}

	#remedy(work, episode) {
		return "release the exact claim with `release work="
			+ (work ?? "WORK") + " expect=" + this.participant
			+ " episode=" + (Number.isSafeInteger(episode) ? episode : "N")
			+ " reason=…` — a Route handler, or a member of the owning team "
			+ "holding the `recover` capability. Prove any delegated runtime "
			+ "absent FIRST: an ended ACP turn is not evidence that an "
			+ "external container ended.";
	}

	/** Reconcile one ended ACP turn. Answers whether the lane is now fenced.
	 *
	 *  Called after the process domain is settled and BEFORE `idle`, on every
	 *  outcome — a returned prompt, a provider failure and a transport loss
	 *  alike — because none of the three is a canonical terminal result.
	 */
	async settle(action, { session = null, runtimeLocator = null } = {}) {
		const previous = this.fence;
		if (previous && this.fenced()) {
			// Already stranded, restored-unverified, or not durable. A second
			// observation must not re-mint the record: that would reset the
			// durable acknowledgement and file the same failure again on
			// every repeat.
			return "stranded";
		}
		// `previous` is now either null or a VERIFIED recoverable fence, and
		// W55705 review [P1] is why it is carried into the read rather than
		// cleared before it: the old code set `this.fence = null` and
		// recursed, so the retry had nothing to compare the new authority
		// with, filed an already-acknowledged incident again, and could copy
		// a `true` acknowledgement onto a SUCCESSOR fence for another Work.
		const found = await this.#read(action, previous);
		if (previous && (found.state === "authority-drift"
				|| found.state === "unreadable")) {
			// NOTHING NEW WAS LEARNED, so nothing is replaced. The fence
			// keeps its identity, its instant and its acknowledgement, and
			// only its VERIFIED bit drops — which is what strands the lane
			// until a readable, matching answer arrives.
			return this.#keepUnverified(found, session);
		}
		if (found.state === "released") {
			if (!previous) return "released";
			// The claim this fence described is canonically gone. The marker
			// outlives the process, so a delete nobody could confirm must not
			// become an in-memory clear.
			if (!this.store.clear(this.participant, CLAIM_SLOT)) {
				previous.verified = false;
				return "stranded";
			}
			this.fence = null;
			this.logger.info(
				`${this.participant}'s claim slot is canonically released; `
				+ `the ACP settlement fence is cleared`);
			return "released";
		}
		const minted = this.#mint(found, action, runtimeLocator);
		if (previous && sameFence(previous, minted)) {
			// THE SAME FENCE, RE-OBSERVED. One failure files one incident
			// however many recovery turns it takes, so the acknowledgement
			// and the `since` instant are the previous one's and are not
			// re-minted around them.
			previous.checkedAt = this.now();
			if (runtimeLocator) previous.runtimeLocator = runtimeLocator;
			if (previous.durable === false) {
				previous.durable = this.store.save(
					this.participant, CLAIM_SLOT, this.#record(previous));
			}
			await this.#publish(session);
			await this.fileIncident(session);
			return this.fenced() ? "stranded" : "recoverable";
		}
		// Either the first observation of a surviving claim, or a genuine
		// SUCCESSOR — a different Work, episode, action key or correlation
		// now occupies the one slot. A successor owes its OWN incident and
		// inherits no acknowledgement from the fence it replaced.
		this.fence = minted;
		// DURABLE BEFORE ANYTHING ASYNCHRONOUS. A crash between observing the
		// surviving claim and publishing it must not lose the only notice.
		this.fence.durable = this.store.save(
			this.participant, CLAIM_SLOT, this.#record(this.fence));
		await this.#publish(session);
		await this.fileIncident(session);
		this.logger.error(
			`the ACP turn for ${this.participant} ended while `
			+ `${this.fence.work ?? "a claim"} is still claimed`
			+ (Number.isSafeInteger(this.fence.episode)
				? ` at assignment episode ${this.fence.episode}` : "")
			+ ` (${this.fence.correlation}). Nothing is executing it and the `
			+ `participant's one claim slot is occupied. `
			+ (this.fence.durable === false
				? `The marker could NOT be persisted, so the lane is fenced `
				  + `in this process only and readiness is RETAINED. `
				: "")
			+ (runtimeLocator
				? `A delegated runtime was reported at ${runtimeLocator}. `
				: `Any delegated runtime this turn started is NOT proved `
				  + `absent by the ACP turn ending. `)
			+ this.fence.remedy);
		// THE VERDICT THE CALLER ACTS ON, and the three words are the whole
		// division of labour between this Work and W11910:
		//   `released`    nothing survived; publish `idle` and acknowledge.
		//   `recoverable` the authority still offers this Work to this
		//                 participant, so the ordinary offer lifecycle
		//                 continues and re-delivery is the recovery — but the
		//                 runner is `failed`, not `idle`, and an incident is
		//                 owed.
		//   `stranded`    the one claim slot is occupied by something this
		//                 offer cannot become; retain readiness.
		return this.fenced() ? "stranded" : "recoverable";
	}

	/** An opaque answer against an existing fence: keep everything, drop the
	 *  verification, retry the incident.
	 *
	 *  W55705 review [P1]: minting a fresh `unreadable` fence here would give
	 *  the SAME stranded claim a second identity and therefore a second
	 *  incident, and would throw away the authority the first read recorded.
	 *  "I could not ask" is not a new fact about the slot.
	 */
	async #keepUnverified(found, session) {
		this.fence.verified = false;
		if (found.state === "authority-drift") {
			this.fence.drift = found.found ?? null;
			this.logger.error(
				`the ACP claim settlement fence for ${this.participant} was `
				+ `taken against authority ${found.expected} and the canonical `
				+ `read answered from ${found.found ?? "an unnamed authority"}; `
				+ `the lane stays fenced rather than treating drift as release`);
		}
		await this.#publish(session);
		await this.fileIncident(session);
		return "stranded";
	}

	#mint(found, action, runtimeLocator = null) {
		const fence = {
			since: this.now(),
			authority: found.authority ?? null,
			work: found.work ?? action?.work ?? null,
			episode: Number.isSafeInteger(found.episode) ? found.episode
				: (Number.isSafeInteger(action?.episode_seq)
					? action.episode_seq : null),
			actionKey: found.actionKey ?? action?.action_key ?? null,
			correlation: found.state,
			// THE OFFER, KEPT APART FROM THE OCCUPANT. For a `secondary`
			// fence the two are different Work, and only the OFFER can be
			// asked about again: a later read classified against the
			// occupant would find that occupant "claimed" and quietly
			// re-admit delivery into a slot that never freed. Correlation is
			// a fact about the delivered assignment, so the question that
			// re-derives it has to be the delivered assignment's.
			offered: {
				work: action?.work ?? null,
				episode: Number.isSafeInteger(action?.episode_seq)
					? action.episode_seq : null,
				actionKey: action?.action_key ?? null,
			},
			runtimeLocator: runtimeLocator ?? null,
			incidentFiled: false,
			restored: false,
			// Minted from a canonical read this process just performed
			// against its own configured authority, so it is verified by
			// construction — unlike a marker restored from disk.
			verified: true,
			durable: false,
			checkedAt: this.now(),
		};
		fence.remedy = this.#remedy(fence.work, fence.episode);
		return fence;
	}

	/** One canonical read, compared against the fence it must answer FOR.
	 *
	 *  W55705 review [P1]: the comparison base is an explicit operand rather
	 *  than `this.fence`, because the retry path used to null the fence
	 *  before reading and therefore compared against nothing at all.
	 */
	async #read(action, against = null) {
		let payload;
		try {
			payload = await this.readSlot();
		} catch (error) {
			this.logger.error(
				`could not reconcile ${this.participant}'s claim after an ACP `
				+ `turn: ${error.message}; the lane is fenced rather than `
				+ `reported idle`);
			return { state: "unreadable" };
		}
		const found = classifySlot(payload, action);
		if (found.state === "unreadable") {
			this.logger.error(
				`reconciliation for ${this.participant} returned no actionable `
				+ `set; the lane is fenced rather than reported idle`);
			return found;
		}
		const expected = against?.authority ?? null;
		if (expected && found.authority !== expected) {
			// AN UNNAMED AUTHORITY IS NOT A MATCH EITHER. A projection that
			// dropped the field cannot confirm that this answer is about the
			// authority the fence was taken against, and the ruling makes
			// that fail closed rather than lenient.
			return { ...found, state: "authority-drift",
				expected, found: found.authority ?? null };
		}
		return found;
	}

	async #publish(session) {
		// The honest runner state beside a surviving claim is `failed`, never
		// `idle`. `internal` is the closed cause: the bridge's own delivery
		// ended without the claim being settled, which is not an approval, a
		// credential, a provider or a transport fault.
		try {
			await this.runtime.state("failed", {
				cause: "internal",
				work: this.fence.work ?? undefined,
				episode: Number.isSafeInteger(this.fence.episode)
					? this.fence.episode : undefined,
				session: session ?? undefined,
				detail: "an ACP turn ended while this participant still holds "
					+ "an active claim; the Work is still claimed and nothing "
					+ "is executing it",
			});
		} catch (error) {
			this.logger.warn(
				`the fenced runtime state for ${this.participant} could not be `
				+ `published: ${error.message}; the fence itself still holds`);
		}
	}

	/** File the one sticky incident, and answer whether it is now durable.
	 *
	 *  RETRYABLE ON PURPOSE. `incident()` answers false when the publication
	 *  is refused — including when this runner has no configured action owner,
	 *  which W55705's own deployment hit — and a throw is a transport fault.
	 *  Neither may be recorded as filed, because the acknowledgement is what
	 *  makes the next reconcile skip it.
	 *
	 *  SERIALIZED, and W55705 review (2026-09-01T03:41:20Z) [P1] is why:
	 *  `settle` and `reconcile` can both reach this, and two publications in
	 *  flight for one fence is two incidents for one stranded claim.
	 */
	async fileIncident(session = null) {
		if (!this.fence || this.fence.incidentFiled) return false;
		if (this.filing) return await this.filing;
		const target = this.fence;
		this.filing = this.#fileOnce(target, session);
		try {
			return await this.filing;
		} finally {
			this.filing = null;
		}
	}

	async #fileOnce(target, session) {
		let ok = false;
		try {
			ok = await this.runtime.incident({
				cause: "internal", category: "other",
				detail: "an ACP turn ended while this participant still holds "
					+ "an active claim; nothing is executing it and the one "
					+ "claim slot is occupied"
					+ (target.runtimeLocator
						? `; a delegated runtime was reported at `
						  + `${target.runtimeLocator}`
						: "; any delegated runtime is not proved absent"),
				work: target.work ?? undefined,
				episode: Number.isSafeInteger(target.episode)
					? target.episode : undefined,
				actionKey: target.actionKey ?? undefined,
				session: session ?? undefined,
			});
		} catch (error) {
			this.logger.error(
				`the ACP orphaned-claim incident for ${this.participant} threw `
				+ `(${error.message}); it stays unfiled and is retried`);
			return false;
		}
		if (!ok) {
			this.logger.error(
				`the ACP orphaned-claim incident for ${this.participant} could `
				+ `NOT be recorded; the operator has no durable notice that a `
				+ `claim is stranded. It stays unfiled and is retried.`);
			return false;
		}
		// A LATE ACKNOWLEDGEMENT BELONGS TO THE FENCE THAT ASKED FOR IT.
		// W55705 review [P1]: the retry path could copy a `true` onto a
		// SUCCESSOR fence for another Work and episode, which suppressed the
		// incident the successor was owed. Identity is checked here rather
		// than assumed from "there is still a fence".
		if (!this.fence || !sameFence(this.fence, target)) {
			this.logger.warn(
				`an ACP orphaned-claim incident for ${this.participant} `
				+ `landed after its fence was replaced; the acknowledgement `
				+ `is NOT transferred and the current fence still owes its own`);
			return false;
		}
		this.fence.incidentFiled = true;
		// AND IT IS NOT DURABLE UNTIL THE MARKER SAYS SO. An acknowledgement
		// only in memory means a restart files the same incident again, so an
		// uncommitted save strands the lane rather than being ignored.
		if (!this.store.save(this.participant, CLAIM_SLOT,
				this.#record(this.fence))) {
			this.fence.durable = false;
			return false;
		}
		return true;
	}

	/** Bounded re-check while fenced.
	 *
	 *  Clears ONLY on a canonical released answer whose delete was confirmed.
	 *  An unreadable or drifted answer leaves the fence exactly where it was,
	 *  and a DIFFERENT occupant mints a successor that owes its own incident —
	 *  W55705 review [P1]: a fence for W1/episode 11 followed by a canonical
	 *  W2/episode 22 used to stay filed against W1 and emit nothing for W2.
	 */
	async reconcile({ force = false } = {}) {
		const previous = this.fence;
		if (!previous) return "clear";
		const due = force || previous.checkedAt === 0
			|| (this.now() - previous.checkedAt) >= RECONCILE_MS;
		if (!due) return "fenced";
		previous.checkedAt = this.now();
		// THE OFFER IS WHAT IS ASKED ABOUT AGAIN, never the occupant. See
		// `#mint`: classifying a `secondary` fence against the Work that took
		// the slot would report that Work as "claimed" and clear the fence
		// for a slot that never freed.
		const offer = previous.offered ?? { work: previous.work,
			episode: previous.episode, actionKey: previous.actionKey };
		const action = { work: offer.work, episode_seq: offer.episode,
			action_key: offer.actionKey };
		const found = await this.#read(action, previous);
		if (found.state === "authority-drift" || found.state === "unreadable") {
			await this.#keepUnverified(found, null);
			return "fenced";
		}
		if (found.state === "released") {
			if (!this.store.clear(this.participant, CLAIM_SLOT)) {
				// The marker outlives the process, so a delete nobody could
				// confirm must not become an in-memory clear.
				previous.verified = false;
				return "fenced";
			}
			this.fence = null;
			this.logger.info(
				`${this.participant}'s claim slot is canonically released; the `
				+ `ACP settlement fence is cleared and delivery resumes`);
			return "clear";
		}
		const minted = this.#mint(found, action, previous.runtimeLocator);
		if (sameFence(previous, minted)) {
			// THE SAME FENCE. This is also where a RESTORED marker meets the
			// authority this process is configured against and becomes
			// deliverable-if-recoverable — never before.
			previous.verified = true;
			previous.restored = false;
			if (previous.durable === false) {
				previous.durable = this.store.save(
					this.participant, CLAIM_SLOT, this.#record(previous));
			}
			await this.fileIncident();
			return "fenced";
		}
		// A SUCCESSOR occupies the one slot. It is a different stranded fact
		// and owes its own incident; the predecessor's acknowledgement is not
		// transferred to it.
		this.fence = minted;
		this.fence.durable = this.store.save(
			this.participant, CLAIM_SLOT, this.#record(this.fence));
		await this.#publish(null);
		await this.fileIncident();
		this.logger.error(
			`${this.participant}'s claim slot is now occupied by `
			+ `${this.fence.work ?? "another claim"}`
			+ (Number.isSafeInteger(this.fence.episode)
				? ` at assignment episode ${this.fence.episode}` : "")
			+ ` (${this.fence.correlation}); the earlier fence is superseded `
			+ `and this one owes its own incident. ${this.fence.remedy}`);
		return "fenced";
	}
}

/** Whether two fences are the SAME stranded fact.
 *
 *  W55705 review (2026-09-01T03:41:20Z) [P1]. The acknowledgement, the
 *  `since` instant and the one-incident rule all hang on this answer, so it
 *  compares every field an operator would have to act on separately: a
 *  different authority, Work, episode, action key or correlation is a
 *  different thing to recover, and inherits nothing from its predecessor.
 */
function sameFence(a, b) {
	return a.authority === b.authority
		&& a.work === b.work
		&& a.episode === b.episode
		&& a.actionKey === b.actionKey
		&& a.correlation === b.correlation;
}
