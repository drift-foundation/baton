// The manager control store: one transaction boundary and one journal.
//
// W2929. The shape follows the authority's `store.mjs` deliberately —
// `transact` is the atomic boundary and `replay` is what makes a repeated
// request return the first outcome instead of performing it twice. They
// are one mechanism: journalling outside the transaction that did the work
// would let a crash leave a mutation with no operation record, and the next
// retry would do it again.
//
// TWO KINDS OF REFUSAL, and they need opposite storage. An ORDINARY
// refusal wrote nothing and stays retryable, so its partial writes must
// vanish. A DURABLE refusal — cleanup blocked on intake is the contract's
// example — is itself a committed outcome, so its writes and the refusal
// record must survive and the retry must replay the refusal rather than
// re-deciding it. The action therefore runs inside a savepoint.

import { DatabaseSync } from "node:sqlite";

import { assertNoDurableSecret, ContractError, digest } from "./contracts.mjs";
import { SCHEMA, SCHEMA_VERSION } from "./schema.mjs";

export class ControlStore {
	#db;

	#clock;

	constructor(path, { incarnation, clock = () => new Date().toISOString() } = {}) {
		if (typeof path !== "string" || path.length === 0) {
			throw new ContractError("integrity", "path",
				"the control store needs an explicit path; there is no ambient "
				+ "default, and one pointing into the checkout is exactly what "
				+ "the external state root exists to prevent");
		}
		if (typeof incarnation !== "string" || incarnation.length === 0) {
			throw new ContractError("integrity", "schema",
				"a manager instance names its incarnation");
		}
		// Review 2026-08-22 [P2]: this executed the whole schema — and
		// changed journal mode — BEFORE reading the recorded version, so
		// opening a store this build cannot speak added five tables to it on
		// the way to refusing. An incompatible binary must INSPECT and refuse
		// without changing anything, and the throwing constructor must not
		// leave its handle open either.
		//
		// So the two cases are separated: validate an existing store, and
		// initialize a fresh one atomically. The busy policy goes in force
		// before any lock is taken, because the initializing transaction is
		// itself a lock-taker.
		this.#db = new DatabaseSync(path);
		try {
			this.#db.exec("PRAGMA busy_timeout = 5000");
			// Round-3 review [P2]: this asked only whether `meta` EXISTS,
			// and treated its absence as proof the file was new. Absence of
			// Baton's metadata is not evidence that a database belongs to
			// Baton — it is equally the signature of somebody else's store.
			// A pre-existing file holding `foreign_state` was adopted and
			// came back carrying both that table and every manager table.
			//
			// So the question is ownership, not presence: a GENUINELY EMPTY
			// schema is initialized; anything else must carry the manager's
			// own metadata or be refused without a byte changed.
			const objects = this.#db.prepare(
				"SELECT name FROM sqlite_master "
				+ "WHERE name NOT LIKE 'sqlite_%'").all();
			if (objects.length === 0) {
				this.#initialize();
			} else if (objects.some(({ name }) => name === "meta")) {
				this.#validate(path);
			} else {
				throw new ContractError("integrity", "schema",
					`the database at ${path} already holds `
					+ `${objects.length} object(s) and none is this `
					+ `manager's metadata, so it is not a control store `
					+ `this build owns. Nothing was changed`);
			}
		} catch (failure) {
			// Close on EVERY constructor failure. A refused open that leaked
			// a handle would hold a lock on a store this build has just said
			// it must not touch.
			try { this.#db.close(); } catch { /* already closed */ }
			throw failure;
		}
		this.incarnation = incarnation;
		this.#clock = clock;
	}

	#initialize() {
		// One transaction: a crash mid-DDL leaves no half-built store for
		// the next process to mistake for a compatible one.
		this.#db.exec("BEGIN IMMEDIATE");
		try {
			this.#db.exec(SCHEMA);
			this.#db.prepare("INSERT INTO meta (key, value) VALUES (?, ?)")
				.run("schema_version", String(SCHEMA_VERSION));
			this.#db.exec("COMMIT");
		} catch (failure) {
			try { this.#db.exec("ROLLBACK"); } catch { /* nothing open */ }
			throw failure;
		}
		// WAL is a database-level property and cannot be set inside a
		// transaction; it is applied only to a store this build now owns.
		this.#db.exec("PRAGMA journal_mode = WAL");
		this.#db.exec("PRAGMA foreign_keys = ON");
	}

	#validate(path) {
		const found = this.#db.prepare(
			"SELECT value FROM meta WHERE key='schema_version'").get();
		if (found === undefined || Number(found.value) !== SCHEMA_VERSION) {
			throw new ContractError("integrity", "schema",
				`control store at ${path} is schema `
				+ `${found?.value ?? "unrecorded"}; this build is `
				+ `${SCHEMA_VERSION} and does not guess across versions. `
				+ `Nothing was changed`);
		}
		this.#db.exec("PRAGMA foreign_keys = ON");
	}

	close() { this.#db.close(); }

	get db() { return this.#db; }

	/** The manager's injected clock.
	 *
	 *  Exposed so an act built ON this store stamps its rows from the SAME
	 *  instant source the journal does. A module reaching for wall time of
	 *  its own would put two clocks in one manager, and a fixture that
	 *  pinned one would silently not pin the other. */
	get clock() { return this.#clock; }

	/** One atomic manager act, journalled by its operation identity.
	 *
	 *  `signature` is the FULL effective signature of the operation, not
	 *  its id: §4.2 says reusing an id with a different signature is
	 *  `refused.operation-collision` and changes nothing. That check is
	 *  made HERE, inside the transaction, because two managers can reach
	 *  it concurrently and a read-then-write check outside would let both
	 *  through. */
	transact(operationId, kind, signature, action) {
		if (typeof operationId !== "string" || operationId.length === 0) {
			throw new ContractError("integrity", "schema",
				"every mutating manager act carries an operation identity");
		}
		const peek = this.replay(operationId, signature);
		if (peek.found) return peek.value;
		this.#db.exec("BEGIN IMMEDIATE");
		try {
			// Re-read inside the lock. The optimistic peek above answers the
			// common case without a write lock; this is the one that decides.
			const again = this.replay(operationId, signature);
			if (again.found) {
				this.#db.exec("ROLLBACK");
				return again.value;
			}
			this.#db.exec("SAVEPOINT act");
			let result;
			try {
				result = action(this.#db);
			} catch (failure) {
				if (failure instanceof ContractError && failure.durable === true) {
					// A refusal that wrote something durable: keep the writes,
					// record the refusal, and commit. The retry replays it.
					this.#db.exec("RELEASE act");
					// The same durable discipline for the sealed refusal: its
					// message and operation state are journalled and replayed
					// verbatim, so they are durable surfaces too.
					this.#record(operationId, kind, signature, "refused", null,
					             _durable(sealRefusal(failure),
					                      "a sealed refusal").bytes);
					this.#db.exec("COMMIT");
					throw failure;
				}
				this.#db.exec("ROLLBACK TO act");
				this.#db.exec("ROLLBACK");
				throw failure;
			}
			this.#db.exec("RELEASE act");
			// Round-3 review [P1]: the journal is a DURABLE surface and the
			// check that says so was never applied to it. A result carrying
			// the bearer under a nested field was serialized straight into
			// `operations.result` and committed; the file-wide sweep proved
			// only that its own one safe action was safe.
			//
			// Inside the transaction, so a refusal takes the action's writes
			// with it — a committed mutation whose journal row was rejected
			// would be the effectively-once mechanism's worst state: done,
			// unrecorded, and repeatable.
			const durable = _durable(result ?? null, "an operation result");
			this.#record(operationId, kind, signature, "committed",
			             durable.bytes, null);
			this.#db.exec("COMMIT");
			// The COMMITTED answer, not the action's object. An exact retry
			// replays these same bytes, so the first caller and every later
			// one are told the same thing.
			return durable.committed;
		} catch (failure) {
			try { this.#db.exec("ROLLBACK"); } catch { /* already settled */ }
			throw failure;
		}
	}

	/** `{ found, value }` for one operation identity.
	 *
	 *  Re-review 2026-08-22 [P1]: this answered `null` for BOTH "no row" and
	 *  "the committed result was JSON null", so an exact retry of a
	 *  null-returning operation looked new, ran the action a second time, and
	 *  only then hit the journal's primary key. Effectively-once cannot be
	 *  built on a value that also means absence — presence is its own fact
	 *  and is returned as one.
	 *
	 *  BYTE-STABLE: the stored JSON is returned as it was recorded, not
	 *  recomputed. A result rebuilt from current state would be a fresh
	 *  answer wearing the first one's identity. */
	replay(operationId, signature) {
		const row = this.#db.prepare(
			"SELECT kind, signature, state, result, refusal FROM operations "
			+ "WHERE operation_id = ?").get(operationId);
		return this.#decide(operationId, signature, row);
	}

	#decide(operationId, signature, row) {
		if (row === undefined) return { found: false, value: null };
		if (row.signature !== signature) {
			throw new ContractError("refused", "operation-collision",
				`operation ${operationId} is already committed with a different `
				+ `signature; reusing an id with different operands changes `
				+ `nothing (§4.2)`);
		}
		if (row.state === "refused") {
			// The FIRST answer, reproduced. Rebuilding it as
			// `refused.precondition` would give the retry a different
			// portable meaning and a different retry policy — which is not
			// a replay of the same refusal, however faithfully the message
			// was kept.
			throw reviveRefusal(row.refusal);
		}
		return { found: true,
		         value: row.result === null ? null : JSON.parse(row.result) };
	}

	#record(operationId, kind, signature, state, result, refusal) {
		this.#db.prepare(
			"INSERT INTO operations (operation_id, kind, signature, state, "
			+ "result, refusal, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
			// The MANAGER's clock, injected. Every row used to record the
			// epoch, so the journal carried no settlement evidence at all.
			.run(operationId, kind, signature, state, result, refusal,
			     this.#clock());
	}

	operationRecord(operationId) {
		return this.#db.prepare(
			"SELECT * FROM operations WHERE operation_id = ?")
			.get(operationId) ?? null;
	}
}

/** The exact bytes to journal, proven free of durable secrets.
 *
 *  Round-5 review [P1]: the walk read the action's OBJECT and `JSON.stringify`
 *  read it again for the row. Two observable reads of a value the manager did
 *  not construct: a `toJSON` method can return `{diagnostic: <bearer>}` while
 *  `Object.entries` shows only the method, so the guard passed and the raw
 *  bearer committed.
 *
 *  The durable boundary is the SERIALIZED REPRESENTATION, not the object it
 *  came from. So it is serialized ONCE, the parse of those exact bytes is what
 *  gets walked — `JSON.parse` runs no user code, so the walk sees precisely
 *  what will be stored — and the same bytes are recorded without
 *  reserialization. Reserializing after validation would reopen the gap for a
 *  stateful `toJSON` or getter. */
function _durable(value, where) {
	const bytes = JSON.stringify(value ?? null);
	const committed = JSON.parse(bytes);
	assertNoDurableSecret(committed, where);
	// BOTH, from the ONE serialization. Round-6 review [P1]: the bytes were
	// recorded and the caller's own object was returned, so a `toJSON` made
	// the first answer the mutable source and the retry the parsed journal —
	// two different answers under one operation identity for an act that ran
	// once. `committed` is the durable answer, and it is what every caller
	// gets, first call and replay alike. It is also nobody's alias.
	return { bytes, committed };
}

/** The whole sealed refusal outcome, so a retry reproduces the first answer.
 *
 *  Review 2026-08-22 [P1]: only the message was kept, so replay fabricated
 *  `refused.precondition` for every durable refusal. The closed pair IS the
 *  portable meaning — a `policy.retention` and a `refused.precondition` are
 *  different answers with different retry policies. */
export function sealRefusal(failure) {
	return {
		category: failure.category,
		code: failure.code,
		message: failure.message,
		...(failure.retry === undefined ? {} : { retry: failure.retry }),
		...(failure.operation_state === undefined
			? {} : { operation_state: failure.operation_state }),
	};
}

export function reviveRefusal(sealed) {
	const record = JSON.parse(sealed);
	const refusal = new ContractError(record.category, record.code,
	                                  record.message);
	if (record.retry !== undefined) refusal.retry = record.retry;
	if (record.operation_state !== undefined) {
		refusal.operation_state = record.operation_state;
	}
	refusal.durable = true;
	refusal.replayed = true;
	return refusal;
}

/** The signature of a manager operation.
 *
 *  Deliberately the SAME shape as the wire operation signature — kind plus
 *  durable operands — so a manager reading its own journal and a peer
 *  reading the frame are talking about one identity rather than two that
 *  happen to travel together. */
export function managerSignature(kind, operands) {
	return digest({ kind, operands });
}
