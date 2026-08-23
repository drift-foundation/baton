// The durable store and the effectively-once operation journal.
//
// Two things live here because they are one mechanism. `transact` is the
// atomic boundary the contract keeps insisting on — "ONE transaction:
// fence the exact generation AND end the assignment" — and `replay` is
// what makes a repeated request return the first outcome instead of
// performing it twice. Neither is safe without the other: journalling
// outside the transaction that did the work would let a crash leave a
// mutation with no operation record, and the next retry would do it
// again.
//
// THE SAVEPOINT IS NOT DECORATION. §7 distinguishes two kinds of
// refusal, and they need opposite storage:
//
//   - an ORDINARY refusal writes nothing and stays retryable. Its
//     partial writes, if any, must vanish.
//   - a refusal that WROTE something durable — the stale-target
//     integration journals its attempt before refusing — is itself a
//     committed outcome, so those writes AND the refusal record must
//     survive, and the retry replays the refusal rather than appending a
//     second attempt.
//
// So the action runs inside a savepoint: an ordinary refusal rolls back
// to it, a durable refusal releases it and records the refusal, and both
// then COMMIT the enclosing transaction. A fault that is not a `Refusal`
// takes the whole transaction down instead — an operation whose failure
// we cannot describe is not one we may record an outcome for.
//
// WHICH KIND a refusal is comes from the refusal itself
// (`Refusal.durable`), set by the transition that raised it. Review
// 2026-08-22 [P1]: a per-call-site flag marked every refusal from that
// transition durable, including ones that wrote nothing, permanently
// closing operation identities that should have stayed retryable.

import { DatabaseSync } from "node:sqlite";

import { Refusal } from "./errors.mjs";
import { SCHEMA, SCHEMA_VERSION } from "./schema.mjs";

export class Store {
	#db;
	#depth = 0;
	#savepoints = 0;

	constructor(db) {
		this.#db = db;
	}

	static open(path, { authorityUuid = null } = {}) {
		const db = new DatabaseSync(path);
		// BEFORE the schema, not inside it. Several processes opening one
		// fresh authority contend on the first statement that takes a lock,
		// and a busy timeout declared halfway down the schema is not in
		// force for the statements above it.
		db.exec("PRAGMA busy_timeout = 5000");
		db.exec(SCHEMA);
		const read = db.prepare("SELECT value FROM meta WHERE key = ?");
		const write = db.prepare(
			"INSERT INTO meta (key, value) VALUES (?, ?) "
			+ "ON CONFLICT (key) DO NOTHING");
		write.run("schema_version", String(SCHEMA_VERSION));
		const version = read.get("schema_version")?.value;
		if (version !== String(SCHEMA_VERSION)) {
			db.close();
			throw new Refusal(
				`the authority at ${path} is schema ${version}, not `
				+ `${SCHEMA_VERSION}; this disposable authority does not migrate`);
		}
		// The authority UUID is written ONCE, at creation. Reopening with a
		// different one is refused rather than adopted: every assignment
		// identity in this store names the original, so a store that
		// answered to two UUIDs would make `assignment_ref` ambiguous —
		// which is the one thing §4 says it must never be.
		if (authorityUuid !== null) write.run("authority_uuid", authorityUuid);
		const recorded = read.get("authority_uuid")?.value ?? null;
		if (recorded === null) {
			db.close();
			throw new Refusal(
				`the authority at ${path} has no recorded authority UUID; open it `
				+ `with one to create it`);
		}
		if (authorityUuid !== null && recorded !== authorityUuid) {
			db.close();
			throw new Refusal(
				`the authority at ${path} is ${recorded}, not ${authorityUuid}; an `
				+ `authority UUID is durable and is never reassigned`);
		}
		const store = new Store(db);
		store.authorityUuid = recorded;
		return store;
	}

	close() { this.#db.close(); }

	get db() { return this.#db; }

	prepare(sql) { return this.#db.prepare(sql); }

	get(sql, ...args) { return this.#db.prepare(sql).get(...args); }

	all(sql, ...args) { return this.#db.prepare(sql).all(...args); }

	run(sql, ...args) { return this.#db.prepare(sql).run(...args); }

	// One write transaction. Nested calls join the outer one rather than
	// opening a second, so a transition that composes two helpers still
	// commits exactly once.
	transact(body) {
		if (this.#depth > 0) {
			this.#depth += 1;
			try { return body(); } finally { this.#depth -= 1; }
		}
		this.#db.exec("BEGIN IMMEDIATE");
		this.#depth = 1;
		let committed = false;
		try {
			const value = body();
			this.#db.exec("COMMIT");
			committed = true;
			return value;
		} finally {
			this.#depth = 0;
			if (!committed) this.#db.exec("ROLLBACK");
		}
	}

	#savepoint(body) {
		const name = `sp_${this.#savepoints++}`;
		this.#db.exec(`SAVEPOINT ${name}`);
		try {
			const value = body();
			this.#db.exec(`RELEASE ${name}`);
			return { ok: true, value };
		} catch (error) {
			if (!(error instanceof Refusal)) {
				this.#db.exec(`ROLLBACK TO ${name}`);
				this.#db.exec(`RELEASE ${name}`);
				throw error;
			}
			// The savepoint is left OPEN on a refusal: only the caller knows
			// whether this refusal wrote something it must keep.
			return { ok: false, error, name };
		}
	}

	#record(operationId, signature, state, result, detail) {
		this.run(
			"INSERT INTO operation (operation_id, signature, state, result, detail, "
			+ "recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
			operationId, signature, state,
			state === "committed" ? JSON.stringify(result ?? null) : null,
			detail ?? null,
			new Date().toISOString());
	}

	operationRow(operationId) {
		return this.get("SELECT * FROM operation WHERE operation_id = ?", operationId)
			?? null;
	}

	// What the journal durably says about one identity. Audit-shaped: a
	// retirement's whole job is to say WHICH operation died and why, so
	// the record has to be readable even though `operationResult` answers
	// only for a committed one.
	operationRecord(operationId) {
		const row = this.operationRow(operationId);
		if (row === null) return null;
		return {
			operationId,
			state: row.state,
			signature: row.signature,
			result: row.state === "committed" ? JSON.parse(row.result) : null,
			detail: row.state === "committed" ? null
				: (row.state === "retired" ? JSON.parse(row.detail) : row.detail),
		};
	}

	// Effectively-once over the FULL effective operands.
	//
	// Order matters and is the contract's, not convenience: RETIREMENT is
	// answered before the signature, because §4 makes retirement a
	// property of the operation IDENTITY rather than of one request's
	// operands. A stale submitter must learn the identity is dead, not
	// that its operands disagree — those are different facts and only one
	// of them is true.
	replay(operationId, signature, action) {
		if (typeof operationId !== "string" || operationId === "") {
			throw new Refusal("every mutating operation needs an operation id");
		}
		const outcome = this.transact(() => {
			const prior = this.operationRow(operationId);
			if (prior !== null) {
				if (prior.state === "retired") {
					return { ok: false, error: new Refusal(JSON.parse(prior.detail).reason) };
				}
				if (prior.signature !== signature) {
					return { ok: false,
					         error: new Refusal("operation id was reused for different operands") };
				}
				if (prior.state === "refused") {
					return { ok: false, error: new Refusal(prior.detail) };
				}
				return { ok: true, value: JSON.parse(prior.result), replayed: true };
			}
			const attempt = this.#savepoint(action);
			if (attempt.ok) {
				const value = attempt.value ?? null;
				this.#record(operationId, signature, "committed", value);
				return { ok: true, value, replayed: false };
			}
			if (attempt.error.durable) {
				// KEEP what the action wrote on its way to refusing, and bind
				// the refusal to this identity so the retry replays it rather
				// than appending a second attempt.
				//
				// The RAISING transition decides this, not the caller: only it
				// knows whether it had already written its evidence when it
				// refused. A blanket flag here marks no-write refusals durable
				// and makes them permanent, which is the opposite of the rule.
				this.#db.exec(`RELEASE ${attempt.name}`);
				this.#record(operationId, signature, "refused", null,
					attempt.error.message);
			} else {
				this.#db.exec(`ROLLBACK TO ${attempt.name}`);
				this.#db.exec(`RELEASE ${attempt.name}`);
			}
			return { ok: false, error: attempt.error };
		});
		if (!outcome.ok) throw outcome.error;
		return outcome.value;
	}

	recordRetirement(operationId, signature, record) {
		this.#record(operationId, signature, "retired", undefined,
			JSON.stringify(record));
	}
}
