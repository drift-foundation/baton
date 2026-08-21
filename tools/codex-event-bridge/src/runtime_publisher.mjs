// W93 slice 4 (finding-agent-runtime-state): the adapter half of the
// participant runtime lease.
//
// Slice 3 gave the authority a place to hold what a participant's
// RUNNER is doing — a different question from what its Work is doing,
// and one the Work table structurally cannot answer. This is what fills
// it in: the two bridges already observe every fact it wants, and until
// now they kept those facts in their own logs.
//
// Five rules shape everything here.
//
// EXPLICIT EVENTS ONLY. A publisher reports transitions its adapter
// actually observed. It never infers. `unknown` and `offline` are
// DERIVED by the authority from an expired lease, which is why they are
// refused as input: a runner that has stopped talking cannot report that
// it has stopped talking.
//
// NO AUTO-QUERY. Publishing costs one local invocation of facts the
// adapter is already holding — including the renewal below, which
// re-states what was last observed rather than asking anything. Nothing
// here reads a provider or wakes a model; `poke` remains the path for
// what only the agent can answer.
//
// NEVER BREAK THE WAKE PATH. Every failure is swallowed and logged
// once, here. A refused or impossible report leaves the lease to expire
// into `unknown`, which is the honest outcome — reached without an
// agent losing its Work.
//
// ORDER IS THE POINT (review R7). Adapters fire-and-forget these calls
// from event handlers, and each one is a child process. Left alone,
// `working` can overtake the `runtime-start` that opens the lease and
// `idle` can land before the turn it follows. Every operation therefore
// goes through ONE per-publisher queue, so the authority sees the order
// the adapter observed. A failed entry never poisons the queue.
//
// EVERY MUTATION IS EFFECTIVELY-ONCE (review R12). These are authority
// writes reached through a child process, so the dangerous shape is
// local and ordinary: the CLI commits and then its result is lost. A
// bare retry would submit the same incarnation as a NEW start, the
// authority would refuse it as already live, and the publisher would
// hold a lease it believes does not exist. Every attempt to open THIS
// incarnation's one lease therefore carries the same `op-id`, so an
// ambiguous result replays instead of becoming a second start. Distinct
// observed transitions carry distinct ids, and so does each renewal —
// a renewal that replayed a committed result would not renew anything.
//
// An identity alone is not enough (review R14). The authority compares
// the EFFECTIVE OPERANDS as well as the id, so a retry that rebuilds
// them — substituting a generic rationale for the caller's, or a turn's
// session for the launch session — is a mismatched operation and gets
// refused rather than replayed, leaving the publisher believing no
// lease exists when one may have committed. The lease-opening operation
// is therefore frozen at its first issue and replayed verbatim by every
// explicit, scheduled and state-triggered retry. A later caller cannot
// alter any operand of it.
//
// NOTHING UPSTREAM IS PERSISTED (review R8). Detail is adapter-authored
// and scrubbed. An upstream error message can carry an authorization
// header, an API key, a URL with credentials or a fragment of a
// provider payload, and truncating it bounds the size of the leak
// rather than preventing it.

import { execFile } from "node:child_process";
import { randomUUID } from "node:crypto";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

// The states the authority accepts as REPORTED. `offline` and `unknown`
// are absent on purpose; see the header.
export const RUNTIME_STATES = new Set([
	"idle", "working", "waiting-input", "retrying", "failed",
]);

// The closed cause categories. An adapter picks the one that describes
// what it observed, and authors its own short phrase.
export const RUNTIME_CAUSES = new Set([
	"approval", "credential", "input", "limit", "provider", "transport",
	"internal",
]);

// A runtime detail is a locator and a short explanation, never a log.
const DETAIL_LIMIT = 400;

// The authority's lease is five minutes. Renewing at a third of it
// keeps a live-but-quiet runner current across one lost renewal without
// making the writes frequent enough to notice.
export const RENEW_MS = 100_000;

// R13: how many times a failed lease opening is retried on the timer
// before the publisher stops trying. At the default cadence that is
// something over a quarter of an hour of an authority being
// unreachable, which is long past the point where the problem is the
// deployment rather than a hiccup.
export const MAX_RECOVERIES = 10;

// Anything that reads like a credential is removed before the text can
// become durable state. This is deliberately broad and blunt: the cost
// of over-redacting an adapter's own sentence is a duller diagnostic,
// and the cost of under-redacting is a token in the authority forever.
const SECRETS = [
	// `Bearer …` / `Basic …` FIRST: the header form below would
	// otherwise consume only the scheme word and leave the value
	// standing, which is the whole leak.
	/\b(bearer|basic)\s+\S+/gi,
	// `Authorization: …`, `x-api-key: …`, `token=…`, `secret: …`
	/\b(authorization|proxy-authorization|x-api-key|api[-_]?key|token|secret|password|passwd|pwd|credential)\b\s*[:=]\s*\S+/gi,
	// credentials embedded in a URL
	/\b[a-z][a-z0-9+.-]*:\/\/[^\s/@]+:[^\s/@]+@/gi,
	// long opaque strings: provider keys and session tokens look like
	// this, and nothing an adapter writes about itself does
	/\b[A-Za-z0-9_-]{32,}\b/g,
];

export function safeDetail(text) {
	if (text === undefined || text === null) return undefined;
	let value = String(text).replace(/\s+/g, " ").trim();
	if (!value) return undefined;
	for (const pattern of SECRETS) value = value.replace(pattern, "[redacted]");
	return value.length > DETAIL_LIMIT
		? `${value.slice(0, DETAIL_LIMIT - 1)}…`
		: value;
}

// Review R10: an operator cannot act on "transport" when the truth is
// exhausted quota or an expired credential. The upstream message is
// read to CLASSIFY and then discarded — the returned detail is this
// module's own sentence, never the message.
export function classifyFailure(error) {
	const text = String(error?.message ?? error ?? "").toLowerCase();
	if (/unauthor|forbidden|401|403|invalid[_ -]?api[_ -]?key|credential|authentication|expired token/.test(text)) {
		return { cause: "credential",
			detail: "the provider rejected this runner's credentials" };
	}
	if (/rate[_ -]?limit|429|quota|too many requests|usage limit/.test(text)) {
		return { cause: "limit",
			detail: "the provider is rate-limiting or the quota is spent" };
	}
	if (/overload|503|502|500|server error|unavailable|capacity/.test(text)) {
		return { cause: "provider",
			detail: "the provider reported an overload or a server error" };
	}
	if (/econn|etimedout|socket|network|disconnect|closed|epipe|enotfound|timeout|abort/.test(text)) {
		return { cause: "transport",
			detail: "the connection to the provider failed" };
	}
	return { cause: "internal",
		detail: "the adapter could not complete this turn" };
}

// The authority's instant vocabulary: whole seconds, UTC, `Z`. A
// millisecond field would be refused, and a local offset would be a
// different instant.
export function canonicalInstant(date = new Date()) {
	return `${date.toISOString().slice(0, 19)}Z`;
}


export class RuntimePublisher {
	// `baton` is {binary, config, participant} — the same three facts
	// every other Baton invocation in these bridges names explicitly.
	// `adapter` is the runner FAMILY (`acp`, `codex`), never inferred
	// from the participant's name: one participant may be driven by any
	// conforming adapter, and guessing from an identity is how a roster
	// starts lying.
	constructor(baton, {
		adapter,
		provider,
		model,
		actionOwner,
		incarnation = randomUUID(),
		renewMs = RENEW_MS,
		maxRecoveries = MAX_RECOVERIES,
		execute,
		logger = console,
		signal,
		setTimer = setTimeout,
		clearTimer = clearTimeout,
		now = () => new Date(),
	} = {}) {
		this.baton = baton;
		this.adapter = adapter;
		this.provider = provider;
		this.model = model;
		this.actionOwner = actionOwner;
		this.incarnation = incarnation;
		this.renewMs = renewMs;
		this.logger = logger;
		this.signal = signal;
		this.setTimer = setTimer;
		this.clearTimer = clearTimer;
		this.now = now;
		// R26: when THIS publisher's lease actually opened, by its own
		// clock and recorded after the write returned. The authority
		// refuses a fact observed before the lease it describes, so a
		// static inventory handed over before the lease opened — or
		// before a recovery reopened it — has to be published as
		// observed at lease open rather than at hand-over.
		this.leaseOpenedAt = null;
		// `issued` is set the moment start() is CALLED, so a state
		// queued behind a pending start is still published in order.
		// `started` is set only when the lease actually opened, which
		// is what keeps a transient failure retryable (review R6).
		this.issued = false;
		this.started = false;
		this.ended = false;
		this.last = null;
		this.timer = null;
		this.chain = Promise.resolve();
		// R12: one stable identity for the lease-opening operation, and
		// a counter for everything that is a genuinely new event.
		this.startOpId = `${this.incarnation}:start`;
		// R14: the one immutable lease-opening operation, built once at
		// first issue and replayed byte-for-byte thereafter.
		this.startOperands = null;
		this.sequence = 0;
		// R13: bounded, so a permanently broken deployment stops
		// writing rather than retrying until the process dies. Giving
		// up leaves the authority showing nothing for this
		// participant, which is the honest picture of a runner whose
		// telemetry cannot reach it.
		this.recoveries = 0;
		this.maxRecoveries = maxRecoveries;
		this.execute = execute ?? ((file, args) => execFileAsync(
			file, args, { encoding: "utf8", signal }));
	}

	#instant() {
		return canonicalInstant(this.now());
	}

	// Review R7: ONE queue, in observation order, and a failure inside
	// it is contained rather than poisoning what follows.
	#enqueue(task) {
		const next = this.chain.then(task, task);
		this.chain = next.then(() => undefined, () => undefined);
		return next;
	}

	async #run(verb, operands, what, opId) {
		const argv = ["--config", this.baton.config,
		              "--participant", this.baton.participant, verb];
		for (const [key, value] of Object.entries(
				{ ...operands, "op-id": opId })) {
			if (value === undefined || value === null) continue;
			argv.push(`${key}=${value}`);
		}
		try {
			await this.execute(this.baton.binary, argv);
			return true;
		} catch (error) {
			// Diagnostics must not become an outage.
			this.logger.warn(
				`runtime ${what} could not be published: `
				+ `${error.message}; readiness is unaffected`);
			return false;
		}
	}

	// Opens the lease. A fresh runner reports `idle`: present, and not
	// yet working, which is a different fact from `unknown`.
	//
	// Review R5: the authority requires a rationale whenever a previous
	// incarnation exists, and this module deliberately performs NO
	// authority query — so it cannot know whether one does. Every start
	// therefore carries a generic truthful reason: on a first launch it
	// explains nothing anybody needed explained, and on every restart
	// after that it is exactly what happened.
	async start({ session, rationale } = {}) {
		if (this.ended || this.started) return false;
		this.issued = true;
		// Frozen at FIRST issue, before the queue: a second explicit
		// start with different arguments must not be able to rewrite
		// the operation the first one may already have committed.
		this.startOperands ??= Object.freeze({
			incarnation: this.incarnation,
			adapter: this.adapter,
			provider: this.provider,
			model: this.model,
			session,
			"action-owner": this.actionOwner,
			rationale: safeDetail(rationale)
				?? `${this.adapter} adapter launched; this incarnation `
				+ `replaces any previous lease for this participant`,
		});
		return await this.#enqueue(async () => {
			if (this.started) return false;
			const ok = await this.#run("runtime-start", this.startOperands,
				"start", this.startOpId);
			// Review R6: `started` moves only on success, so a
			// transient failure leaves the publisher retryable instead
			// of silently disabled for the life of the process.
			this.started = ok;
			if (ok) {
				this.leaseOpenedAt = this.#instant();
				this.last = { state: "idle", options: { session } };
				this.#scheduleRenewal();
			} else {
				// R13: an idle runner has no next state to repair its
				// lease with — ACP goes on completing read-only waits
				// and Codex stays connected — so the repair is
				// scheduled rather than waited for.
				this.#scheduleRecovery();
			}
			return ok;
		});
	}

	// One explicit transition. `work` and `episode` CORRELATE the runner
	// with the assignment it believes it is serving; the authority
	// reports its own canonical Handler beside that and never reconciles
	// the two by writing.
	async state(state, options = {}) {
		if (!RUNTIME_STATES.has(state)) {
			throw new Error(`runtime state '${state}' is not reported by `
				+ `an adapter; offline and unknown are derived from an `
				+ `expired lease`);
		}
		if (options.cause !== undefined
				&& !RUNTIME_CAUSES.has(options.cause)) {
			throw new Error(`runtime cause '${options.cause}' is not one `
				+ `of ${[...RUNTIME_CAUSES].join(", ")}`);
		}
		if (!this.issued || this.ended) return false;
		this.last = { state, options };
		return await this.#enqueue(async () => {
			// Review R6: a lease whose opening failed is re-established
			// here rather than leaving every later report writing at
			// nothing. Bounded — one attempt, on the same queue.
			if (!this.started && !await this.#reopen()) return false;
			this.sequence += 1;
			const ok = await this.#run("runtime-state", {
				incarnation: this.incarnation,
				state,
				cause: options.cause,
				detail: safeDetail(options.detail),
				work: options.work,
				episode: options.episode,
				session: options.session,
			}, state, `${this.incarnation}:s${this.sequence}`);
			if (ok) this.#scheduleRenewal();
			return ok;
		});
	}

	// R12/R14: the SAME identity AND the same frozen operands as the
	// first issue. A start whose result was lost replays here instead
	// of arriving as a mismatched operation the authority must refuse.
	// Nothing about the caller's current situation — which turn is
	// running, which session it is on — may leak in.
	async #reopen() {
		if (!this.startOperands) return false;
		const ok = await this.#run("runtime-start", this.startOperands,
			"start", this.startOpId);
		this.started = ok;
		if (ok) {
			// A recovery mints a lease with a NEW opening instant, and
			// anything still queued behind it is observed no earlier.
			this.leaseOpenedAt = this.#instant();
			this.last = this.last ?? {
				state: "idle",
				options: { session: this.startOperands.session },
			};
			this.#scheduleRenewal();
		}
		return ok;
	}

	#scheduleRecovery() {
		if (this.timer) this.clearTimer(this.timer);
		if (this.ended || !this.renewMs) return;
		if (this.recoveries >= this.maxRecoveries) {
			this.logger.warn(
				`runtime lease could not be opened after `
				+ `${this.recoveries} attempts; this participant will `
				+ `report no runtime state until the adapter restarts, `
				+ `and readiness is unaffected`);
			return;
		}
		this.recoveries += 1;
		this.timer = this.setTimer(() => {
			this.timer = null;
			if (this.ended || this.started) return;
			void this.#enqueue(async () => {
				if (this.ended || this.started) return false;
				const ok = await this.#reopen();
				if (!ok) this.#scheduleRecovery();
				return ok;
			});
		}, this.renewMs);
		this.timer?.unref?.();
	}

	// Review R11: a live runner that is quiet is not an absent one. The
	// lease is deliberately bounded, so a bridge that is idling between
	// waits — or inside one long turn — re-states what it LAST OBSERVED
	// before that bound passes. It asks nothing and wakes nobody; it
	// repeats a fact the adapter already published.
	#scheduleRenewal() {
		if (this.timer) this.clearTimer(this.timer);
		if (this.ended || !this.renewMs) return;
		this.timer = this.setTimer(() => {
			this.timer = null;
			if (this.ended || !this.last) return;
			void this.#enqueue(async () => {
				if (this.ended) return false;
				// A renewal is a NEW event with its own identity: one
				// that reused the last id would replay the committed
				// result and renew nothing, which is the opposite of
				// what it is for.
				this.sequence += 1;
				const ok = await this.#run("runtime-state", {
					incarnation: this.incarnation,
					state: this.last.state,
					cause: this.last.options?.cause,
					detail: safeDetail(this.last.options?.detail),
					work: this.last.options?.work,
					episode: this.last.options?.episode,
				}, `${this.last.state} renewal`,
					`${this.incarnation}:r${this.sequence}`);
				this.#scheduleRenewal();
				return ok;
			});
		}, this.renewMs);
		this.timer?.unref?.();
	}

	// W93 slice 6: the safe operational inventory. The key set is
	// closed on the authority side, so an adapter cannot publish its
	// environment here even by accident — and the values are locators
	// the deployment already configured, never anything read from a
	// provider or a model.
	async facts(supplied = {}, { source = "reported", answers,
	                             observedAt } = {}) {
		if (!this.issued || this.ended) return false;
		// A STATED instant is the caller's claim and is never rewritten
		// — if it predates the lease the authority is right to refuse
		// it. Only the default, "I am handing you what I hold now", is
		// floored, because that claim is still true at lease open.
		const stated = observedAt !== undefined;
		const collectedAt = observedAt ?? this.#instant();
		// W93 review R23: the instant belongs to the OBSERVATION, so it
		// is stamped here — where the caller handed the facts over —
		// and not when the queued write finally runs. Everything below
		// may wait behind a renewal, a recovery, or a retry, and the
		// authority would otherwise record the commit time and call
		// stale facts fresh. Frozen into the operands means a retry
		// replays the same instant, which is what `op-id` requires and
		// what makes a queued publication honest about its own age.
		const operands = { incarnation: this.incarnation, source,
		                   answers };
		let any = false;
		for (const [key, value] of Object.entries(supplied)) {
			if (value === undefined || value === null) continue;
			operands[key] = safeDetail(value);
			any = true;
		}
		if (!any) return false;
		// W93 review R27: the identity is RESERVED at issue, not read
		// from the shared counter when the queued callback finally
		// runs. The dispatcher hands over its startup inventory
		// without awaiting it, so a refresh can be issued while that
		// publication is still queued — and both callbacks would then
		// interpolate the counter's final value, making the second
		// event an exact-`op-id` replay of the first with different
		// operands. The authority is right to refuse that, and the
		// refresh would stay unanswered although its adapter answered
		// it. One event, one immutable identity, closed over here.
		this.sequence += 1;
		const opId = `${this.incarnation}:f${this.sequence}`;
		return await this.#enqueue(async () => {
			if (!this.started && !await this.#reopen()) return false;
			// R26: the two contracts made to agree. The instant is the
			// caller's, floored at the lease it describes — a startup
			// inventory handed over while the lease was still opening,
			// or one waiting behind a recovery that crossed a second
			// boundary, is observed AT lease open rather than refused
			// for predating it. Floors, never rewrites: a genuinely
			// older observation keeps its own instant and the
			// authority is right to refuse it.
			const observed = !stated && this.leaseOpenedAt
				&& collectedAt < this.leaseOpenedAt
				? this.leaseOpenedAt : collectedAt;
			return await this.#run("runtime-facts",
				{ ...operands, "observed-at": observed }, "facts",
				opId);
		});
	}

	// The explicit goodbye. A lease that ends reads `offline` with
	// provenance `reported`, which is a different operational fact from
	// one that simply went quiet.
	//
	// Review R10: a clean exit carries NO cause. The authority's own
	// documentation says a runner that exited cleanly did not fail, and
	// `internal` is reserved for an observed internal failure.
	// W415: the DURABLE half of an approval failure.
	//
	// `state("waiting-input", {cause: "approval"})` is honest and
	// transient — it says what the runner is doing right now, and it is
	// correct for it to disappear when the runner returns to `idle`.
	// That is exactly what erased the evidence three times: the turn
	// ended, the lease moved on, the Inbox row went with it, and the
	// Work sat unclaimed with the only explanation in a rollout nobody
	// reads.
	//
	// So the adapter files a separate incident that OUTLIVES the
	// transition. It is not a second copy of the state; it is the other
	// question. Like every other report here it is best-effort and
	// never breaks the wake path — but unlike a state report, failing
	// to publish it loses an operator's only durable notice, so it says
	// so loudly in the log.
	//
	// The COMMAND BODY IS NEVER SENT. An approval payload can carry
	// credentials, environment values and file contents; what travels
	// is the closed safe category and a scrubbed one-line detail.
	async incident({ cause = "approval", category = "other", detail,
	                 work, episode, actionKey, session } = {}) {
		if (this.ended) return false;
		if (!this.actionOwner) {
			// The finding forbids guessing an owner, and the authority
			// refuses an ownerless incident. Say why here rather than
			// letting it look like a transport failure.
			this.logger.warn(
				`a managed-turn ${cause} incident could not be filed: `
				+ `this runner has no configured action owner, so the `
				+ `incident would be a loose end nobody is holding`);
			return false;
		}
		// W415 review round 2: ONE operation id per OBSERVED occurrence,
		// not per (cause, category, work, episode). The stable id made a
		// second approval request in the same episode replay the first
		// committed result — so it never reached the authority's
		// coalescing update and `occurrences` never advanced past 1. The
		// count is the whole point of coalescing: "this has happened
		// three times" is what says the first repair did not hold.
		//
		// The id is minted HERE, before the queue, so every retry of
		// THIS publication keeps it — transport retry and a newly
		// observed occurrence stay distinguishable, which is the ruled
		// model.
		this.incidentSeq = (this.incidentSeq ?? 0) + 1;
		const opId = `${this.incarnation}:incident:${this.incidentSeq}`;
		return await this.#enqueue(async () => {
			const ok = await this.#run("incident", {
				incarnation: this.incarnation,
				cause, category,
				detail: safeDetail(detail),
				work, episode,
				"action-key": actionKey,
				session,
			}, "incident", opId);
			if (!ok) {
				this.logger.error(
					`the managed-turn ${cause} incident for `
					+ `${this.baton.participant} could NOT be recorded; `
					+ `the operator has no durable notice that this turn `
					+ `failed and the Work is still unclaimed`);
			}
			return ok;
		});
	}

	async end({ cause, detail } = {}) {
		if (!this.issued || this.ended) return false;
		this.ended = true;
		if (this.timer) this.clearTimer(this.timer);
		this.timer = null;
		return await this.#enqueue(async () => {
			if (!this.started) return false;
			return await this.#run("runtime-end", {
				incarnation: this.incarnation,
				cause,
				detail: safeDetail(detail),
			}, "end", `${this.incarnation}:end`);
		});
	}
}

// A publisher that does nothing, for deployments that have not
// configured one. The bridges call the same methods either way rather
// than testing for null at every transition.
export const silentPublisher = {
	incarnation: null,
	async start() { return false; },
	async state() { return false; },
	async facts() { return false; },
	async incident() { return false; },
	async end() { return false; },
};

export function makeRuntimePublisher(baton, options = {}) {
	if (!baton?.binary || !baton?.config || !baton?.participant) {
		return silentPublisher;
	}
	return new RuntimePublisher(baton, options);
}
