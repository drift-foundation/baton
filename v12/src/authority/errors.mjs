// One refusal type for the whole v12 authority.
//
// A `Refusal` is an ORDINARY outcome: a precondition did not hold, an
// operand was stale, an identity collided. It is thrown so no caller can
// mistake it for success, and it is caught by the operation journal,
// which decides whether the refusal wrote anything durable.
//
// Anything that is NOT a `Refusal` escaping a transition is a fault. The
// store rolls the whole transaction back rather than journalling it,
// because an operation whose failure we cannot describe is not one we
// may record an outcome for.

export class Refusal extends Error {
	// `durable` is set by the transition that RAISES the refusal, and only
	// when that transition has already written something it must keep — the
	// stale-target integration journals its attempt before refusing.
	//
	// Review 2026-08-22 [P1]: this used to be a flag on the CALL SITE, so
	// `integrate` marked every refusal durable, including the ones that
	// wrote nothing. A pre-approval integration then recorded a permanent
	// REFUSED row for an operation that had not touched the store, which
	// inverts the contract's rule: an ordinary refusal writes nothing and
	// stays retryable, and REFUSED exists only when the refusal itself is a
	// committed outcome. Only the raising site knows which it was, so only
	// the raising site may say so.
	constructor(message, { code = null, durable = false } = {}) {
		super(message);
		this.name = "Refusal";
		this.code = code;
		this.durable = durable;
	}
}

export function refuse(message, options) {
	throw new Refusal(message, options);
}
