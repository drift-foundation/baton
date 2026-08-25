// W2929: the manager's own durable control store.
//
// Real SQLite files, not process-memory doubles — the acceptance boundary
// asks for that specifically, and the two properties that matter most here
// (one nonterminal offer per Work across manager PROCESSES, and a bearer
// never reaching the file) are properties of the database rather than of
// the code that writes it.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { DatabaseSync } from "node:sqlite";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import {
	ContractError, GOLDEN_BEARER, GOLDEN_VERIFIER, digest, tokenVerifier,
} from "../src/worker_manager/contracts.mjs";
import { ControlStore, managerSignature } from "../src/worker_manager/store.mjs";
import { SCHEMA_VERSION } from "../src/worker_manager/schema.mjs";

after(removeOwnedRoots);

const WORK = "43c55d4b-W1439";
const UUID = "43c55d4b1234567890abcdef12345678";

function storePath(prefix = "v12-manager-") {
	return join(ownedTemp(prefix), "control.sqlite3");
}

function open(path, incarnation = "manager-1") {
	return new ControlStore(path, { incarnation });
}

function issueOffer(db, { offerId, state = "issued", attempt = "attempt-1",
                          work = WORK }) {
	db.prepare(
		"INSERT INTO offers (offer_id, work_id, authority_uuid, participant, "
		+ "runtime_attempt_id, incarnation, readiness_episode, input_digest, "
		+ "policy_digest, profile_digest, verifier, issued_at, expires_at, "
		+ "state) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
		.run(offerId, work, UUID, "poc.claude", attempt, "manager-1", 41,
		     digest(1), digest(2), digest(3), tokenVerifier(GOLDEN_BEARER),
		     "2026-08-22T16:00:00.000Z", "2026-08-22T16:05:00.000Z", state);
}

// -- the store itself --------------------------------------------------------

test("W2929: the control store needs an explicit path and its own schema", () => {
	assert.throws(() => new ControlStore("", { incarnation: "m" }),
		(error) => error instanceof ContractError && error.code === "path");
	const path = storePath();
	const store = open(path);
	try {
		// 14 since W771: posture occupancy separated from the observation
		// axis. Which epoch may run is a MANAGER-owned fact; what the
		// provider was seen to do is evidence, and freeing a posture must
		// never require relabelling the second as the first.
		// Pinned as a literal rather than read from the module, because
		// comparing a build with itself proves nothing about what a store on
		// disk contains.
		assert.equal(store.db.prepare(
			"SELECT value FROM meta WHERE key='schema_version'").get().value,
			String(SCHEMA_VERSION));
		assert.equal(SCHEMA_VERSION, 14);
		// The manager's tables, and NOT the authority's: a manager that
		// stored a claim or a generation would be a second authority.
		const names = new Set(store.db.prepare(
			"SELECT name FROM sqlite_master WHERE type='table'")
			.all().map((row) => row.name));
		for (const table of ["offers", "attempts", "operations",
		                     "observations", "profiles", "meta",
		                     "outputs", "output_artifacts", "manifests",
		                     "intake", "agent_sessions", "turn_allocations",
		                     "turns", "agent_events", "posture_slots"]) {
			assert.ok(names.has(table), table);
		}
		for (const absent of ["work", "assignments", "generations", "gates",
		                      "receipts"]) {
			assert.ok(!names.has(absent),
				`${absent} belongs to the authority, not the manager`);
		}
	} finally {
		store.close();
	}
});

test("W2929: reopening the same file is the whole restart path", () => {
	const path = storePath();
	const first = open(path, "manager-1");
	first.transact("op-1", "offer.issue", managerSignature("offer.issue",
		{ work: WORK }), (db) => {
		issueOffer(db, { offerId: "offer-1" });
		return { offer_id: "offer-1" };
	});
	first.close();
	const second = open(path, "manager-2");
	try {
		assert.equal(second.db.prepare(
			"SELECT state FROM offers WHERE offer_id='offer-1'").get().state,
			"issued");
		// And the journal survives, so the SECOND incarnation replays the
		// first's committed answer rather than re-issuing.
		assert.deepEqual(second.replay("op-1", managerSignature("offer.issue",
			{ work: WORK })), { found: true, value: { offer_id: "offer-1" } });
	} finally {
		second.close();
	}
});

test("W2929: an incompatible store is refused WITHOUT being changed", () => {
	// Review 2026-08-22 [P2]: the old constructor ran the whole schema and
	// changed journal mode before reading the recorded version, so opening a
	// store this build cannot speak added five tables to it on the way to
	// refusing.
	const path = storePath();
	const foreign = new DatabaseSync(path);
	foreign.exec("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)");
	foreign.prepare("INSERT INTO meta (key, value) VALUES (?, ?)")
		.run("schema_version", "99");
	foreign.close();
	const before = readFileSync(path);
	assert.throws(() => open(path), (error) =>
		error instanceof ContractError && error.code === "schema"
		&& /is schema 99/.test(error.message)
		&& /Nothing was changed/.test(error.message));
	// The BYTES, not just the table list: a refused open that changed the
	// journal mode would have rewritten the header.
	assert.deepEqual(readFileSync(path), before,
		"a refused open modified the store it refused");
	const after = new DatabaseSync(path);
	try {
		assert.deepEqual(after.prepare(
			"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
			.all().map((row) => row.name), ["meta"],
			"the refused open added tables to an incompatible store");
	} finally {
		after.close();
	}
	// And the refused open left no handle holding a lock.
	const reopened = new DatabaseSync(path);
	reopened.exec("BEGIN IMMEDIATE");
	reopened.exec("ROLLBACK");
	reopened.close();
});

test("W2929: an existing unowned database is not initialized as fresh", () => {
	// Absence of the manager's `meta` table is not proof that a database is
	// new. Adopting an existing file would mix Baton's tables into somebody
	// else's store before this build had established ownership or compatibility.
	const path = storePath();
	const unowned = new DatabaseSync(path);
	// Match the manager's journal mode so the schema's redundant PRAGMA does
	// not fail incidentally before the ownership decision is exercised.
	unowned.exec("PRAGMA journal_mode=WAL; "
		+ "CREATE TABLE foreign_state (value TEXT NOT NULL)");
	unowned.prepare("INSERT INTO foreign_state VALUES (?)").run("belongs elsewhere");
	unowned.close();
	const before = readFileSync(path);
	assert.throws(() => open(path), (error) =>
		error instanceof ContractError && error.code === "schema");
	assert.deepEqual(readFileSync(path), before,
		"a refused open adopted and changed an existing unowned database");
	const inspected = new DatabaseSync(path);
	try {
		assert.deepEqual(inspected.prepare(
			"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
			.all().map(({ name }) => name), ["foreign_state"]);
	} finally {
		inspected.close();
	}
});

test("W2929: the journal records the MANAGER's clock, not the epoch", () => {
	const instants = ["2026-08-22T18:00:00.000Z", "2026-08-22T18:00:01.000Z"];
	let at = 0;
	const store = new ControlStore(storePath(),
		{ incarnation: "manager-1", clock: () => instants[at++] });
	try {
		store.transact("op-1", "runtime.start",
			managerSignature("runtime.start", { attempt: "a1" }),
			() => ({ runtime_id: "runtime-1" }));
		assert.equal(store.operationRecord("op-1").settled_at, instants[0],
			"the journal carried no settlement evidence");
	} finally {
		store.close();
	}
});

// -- effectively once --------------------------------------------------------

test("W2929: an exact retry replays byte-for-byte and performs nothing", () => {
	const store = open(storePath());
	try {
		const signature = managerSignature("runtime.start", { attempt: "a1" });
		let ran = 0;
		const act = () => store.transact("op-start", "runtime.start", signature,
			() => { ran += 1; return { runtime_id: "runtime-1" }; });
		const first = act();
		const retry = act();
		assert.deepEqual(retry, first);
		assert.equal(ran, 1, "an exact retry performed the act a second time");
	} finally {
		store.close();
	}
});

test("W2929: a committed null result is still a replay, not a missing record", () => {
	// `null` is a valid committed result and also the old replay sentinel.
	// Conflating them re-enters the action on an exact retry, then usually
	// trips over the existing journal row only after the action ran again.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.expire", { offer: "offer-1" });
		let ran = 0;
		const act = () => store.transact("op-null", "offer.expire", signature,
			() => { ran += 1; return null; });
		assert.equal(act(), null);
		assert.equal(act(), null);
		assert.equal(ran, 1, "an exact retry executed a null-returning act twice");
	} finally {
		store.close();
	}
});

test("W2929: a reused id with a different signature is a collision", () => {
	const store = open(storePath());
	try {
		store.transact("op-1", "runtime.start",
			managerSignature("runtime.start", { attempt: "a1" }),
			() => ({ runtime_id: "runtime-1" }));
		assert.throws(() => store.transact("op-1", "runtime.start",
			managerSignature("runtime.start", { attempt: "a2" }),
			() => ({ runtime_id: "runtime-2" })), (error) =>
			error instanceof ContractError
			&& error.category === "refused"
			&& error.code === "operation-collision");
		// …and it CHANGED NOTHING: the first result still stands.
		assert.deepEqual(store.replay("op-1",
			managerSignature("runtime.start", { attempt: "a1" })),
			{ found: true, value: { runtime_id: "runtime-1" } });
	} finally {
		store.close();
	}
});

test("W2929: an ordinary refusal writes nothing and stays retryable", () => {
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.issue", { work: WORK });
		assert.throws(() => store.transact("op-1", "offer.issue", signature,
			(db) => {
				issueOffer(db, { offerId: "offer-1" });
				throw new ContractError("refused", "precondition",
					"the slot is taken");
			}), /the slot is taken/);
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM offers").get().n, 0,
			"an ordinary refusal left its partial writes behind");
		assert.equal(store.operationRecord("op-1"), null,
			"an ordinary refusal closed a retryable operation identity");
		// The same identity is still usable, which is what retryable means.
		store.transact("op-1", "offer.issue", signature, (db) => {
			issueOffer(db, { offerId: "offer-1" });
			return { offer_id: "offer-1" };
		});
		assert.equal(store.db.prepare("SELECT COUNT(*) AS n FROM offers").get().n, 1);
	} finally {
		store.close();
	}
});

test("W2929: a DURABLE refusal survives and the retry replays it", () => {
	// The contract's example is cleanup blocked on intake: it journals its
	// attempt before refusing, so the refusal is itself a committed outcome
	// and a retry must replay it rather than re-deciding.
	const store = open(storePath());
	try {
		const signature = managerSignature("cleanup", { attempt: "a1" });
		let decided = 0;
		const act = () => store.transact("op-clean", "cleanup", signature,
			(db) => {
				decided += 1;
				db.prepare("INSERT INTO attempts (runtime_attempt_id, "
					+ "adapter_name, adapter_digest, profile_digest, created_at) "
					+ "VALUES (?, ?, ?, ?, ?)")
					.run("a1", "scripted", digest(1), digest(2), "2026-08-22");
				// NOT `refused.precondition`: that pair is the one the old
				// replay fabricated, so choosing it as the original would
				// hide the loss the review found.
				const refusal = new ContractError("policy", "retention",
					"cleanup is blocked on intake");
				refusal.retry = "after-state-change";
				refusal.operation_state = "refused";
				refusal.durable = true;
				throw refusal;
			});
		assert.throws(act, (error) => error.category === "policy"
			&& error.code === "retention" && /blocked on intake/.test(error.message));
		assert.equal(store.db.prepare(
			"SELECT COUNT(*) AS n FROM attempts").get().n, 1,
			"a durable refusal lost the writes that made it durable");
		assert.equal(store.operationRecord("op-clean").state, "refused");
		// The REPLAY reproduces the first answer: same closed pair, same
		// retry policy, same operation state. Rebuilding it as
		// `refused.precondition` would give the retry a different portable
		// meaning, which is not a replay of the same refusal.
		assert.throws(act, (error) => error.replayed === true
			&& error.category === "policy" && error.code === "retention"
			&& error.retry === "after-state-change"
			&& error.operation_state === "refused",
			"the retry re-decided a durable refusal, or changed its meaning");
		assert.equal(decided, 1);
	} finally {
		store.close();
	}
});

// -- one offer per Work ------------------------------------------------------

test("W2929: two manager PROCESSES cannot both hold a live offer", () => {
	// The property a read-then-write check cannot give: both managers pass
	// any pre-check, and only the database refuses the second.
	const path = storePath();
	const one = open(path, "manager-1");
	const two = open(path, "manager-2");
	try {
		one.transact("op-a", "offer.issue", managerSignature("offer.issue",
			{ work: WORK, by: "one" }), (db) => {
			issueOffer(db, { offerId: "offer-a" });
			return { offer_id: "offer-a" };
		});
		assert.throws(() => two.transact("op-b", "offer.issue",
			managerSignature("offer.issue", { work: WORK, by: "two" }), (db) => {
				issueOffer(db, { offerId: "offer-b", attempt: "attempt-2" });
				return { offer_id: "offer-b" };
			}), /UNIQUE|constraint/i);
		// An ACCEPTED offer is nonterminal too, so it still blocks a second.
		one.db.prepare("UPDATE offers SET state='accepted' WHERE offer_id=?")
			.run("offer-a");
		assert.throws(() => two.transact("op-c", "offer.issue",
			managerSignature("offer.issue", { work: WORK, by: "three" }), (db) => {
				issueOffer(db, { offerId: "offer-c", attempt: "attempt-3" });
				return null;
			}), /UNIQUE|constraint/i);
		// A TERMINAL one does not: declining frees the Work for a fresh
		// offer, which is the practical point of declining at all.
		one.db.prepare("UPDATE offers SET state='declined' WHERE offer_id=?")
			.run("offer-a");
		two.transact("op-d", "offer.issue", managerSignature("offer.issue",
			{ work: WORK, by: "four" }), (db) => {
			issueOffer(db, { offerId: "offer-d", attempt: "attempt-4" });
			return { offer_id: "offer-d" };
		});
		// A DIFFERENT Work is unaffected throughout.
		two.transact("op-e", "offer.issue", managerSignature("offer.issue",
			{ work: "43c55d4b-W2", by: "five" }), (db) => {
			issueOffer(db, { offerId: "offer-e", attempt: "attempt-5",
			                 work: "43c55d4b-W2" });
			return { offer_id: "offer-e" };
		});
	} finally {
		one.close();
		two.close();
	}
});

// -- the bearer is not in the file -------------------------------------------

test("W2929: no bearer reaches the database, in any column of any table", () => {
	// A property of the FILE, asserted by reading every value back out —
	// "we do not write it" is a property of code, and this is the one the
	// contract actually makes.
	const path = storePath();
	const store = open(path);
	try {
		store.transact("op-1", "offer.issue", managerSignature("offer.issue",
			{ work: WORK }), (db) => {
			issueOffer(db, { offerId: "offer-1" });
			return { offer_id: "offer-1", verifier: GOLDEN_VERIFIER };
		});
		store.db.prepare("UPDATE offers SET decision_reason=? WHERE offer_id=?")
			.run("declined for capacity", "offer-1");
		store.close();
		// Reopened as a plain database, so nothing in the module can hide it.
		const raw = new DatabaseSync(path);
		try {
			const tables = raw.prepare(
				"SELECT name FROM sqlite_master WHERE type='table'").all();
			let inspected = 0;
			for (const { name } of tables) {
				for (const row of raw.prepare(`SELECT * FROM "${name}"`).all()) {
					for (const value of Object.values(row)) {
						inspected += 1;
						if (typeof value !== "string") continue;
						assert.ok(!value.includes(GOLDEN_BEARER),
							`${name} carries the claim bearer`);
					}
				}
			}
			assert.ok(inspected > 0, "the sweep inspected nothing");
			// The verifier IS there, which is what makes the absence above
			// a real assertion rather than an empty table.
			assert.equal(raw.prepare(
				"SELECT verifier FROM offers WHERE offer_id='offer-1'")
				.get().verifier, GOLDEN_VERIFIER);
		} finally {
			raw.close();
		}
	} catch (failure) {
		try { store.close(); } catch { /* already closed */ }
		throw failure;
	}
});

test("W2929: the operation journal refuses a result containing a bearer", () => {
	// The file-wide sweep above proves only that its one safe action was safe.
	// The journal is the durable boundary: an orchestration mistake must not be
	// able to serialize the bearer under a nested secret field.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.accept", { offer: "offer-1" });
		assert.throws(() => store.transact("op-secret", "offer.accept", signature,
			() => ({ accepted: true, nested: { claim_token: GOLDEN_BEARER } })),
			(error) => error instanceof ContractError
				&& error.code === "secret-leak");
		assert.equal(store.operationRecord("op-secret"), null,
			"the refused secret result acquired a durable operation identity");
	} finally {
		store.close();
	}
});

test("W2929 review: a bearer value cannot hide under a non-secret result key", () => {
	// Field-name screening is not a canary scan. The bearer is the secret no
	// matter whether an orchestration mistake calls it `claim_token`,
	// `diagnostic`, or anything else before handing the value to the journal.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.accept", { offer: "offer-1" });
		assert.throws(() => store.transact("op-secret-value", "offer.accept",
			signature, () => ({ accepted: false, diagnostic: GOLDEN_BEARER })),
			(error) => error instanceof ContractError
				&& error.code === "secret-leak");
		assert.equal(store.operationRecord("op-secret-value"), null);
	} finally {
		store.close();
	}
});

test("W2929 review: a durable refusal message cannot contain the bearer", () => {
	// The correction explicitly calls the sealed refusal a durable surface.
	// Its message is persisted verbatim, so checking only the key `message`
	// leaves the same leak open on the refusal path.
	const store = open(storePath());
	try {
		const signature = managerSignature("output.retain", { result: "r1" });
		assert.throws(() => store.transact("op-secret-refusal", "output.retain",
			signature, () => {
				const refusal = new ContractError("policy", "retention",
					`retention refused ${GOLDEN_BEARER}`);
				refusal.durable = true;
				throw refusal;
			}), (error) => error instanceof ContractError
				&& error.code === "secret-leak");
		assert.equal(store.operationRecord("op-secret-refusal"), null);
	} finally {
		store.close();
	}
});

test("W2929 review: the journal checks the exact serialized result", () => {
	// Walking the action's object and serializing it later are two reads of
	// attacker-controlled behavior. `toJSON` can make the durable bytes carry
	// a bearer that was absent from Object.entries during the first read.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.accept", { offer: "offer-1" });
		const result = { toJSON() {
			return { accepted: false, diagnostic: GOLDEN_BEARER };
		} };
		assert.throws(() => store.transact("op-secret-to-json", "offer.accept",
			signature, () => result),
			(error) => error instanceof ContractError
				&& error.code === "secret-leak");
		assert.equal(store.operationRecord("op-secret-to-json"), null,
			"the serialized bearer acquired a durable operation identity");
	} finally {
		store.close();
	}
});


test("W2929: an observation is identified by its FULL source scope", () => {
	// Review 2026-08-22 [P1]: the key was `(attempt, source_seq)`, but the
	// contract scopes `source_seq` to one adapter INCARNATION. A restart —
	// a valid new incarnation beginning again at 1 — collided with the
	// previous incarnation's 1, so the required restart path was
	// indistinguishable from a conflicting duplicate before any monotonic
	// logic ran.
	const store = open(storePath());
	try {
		const db = store.db;
		db.prepare("INSERT INTO attempts (runtime_attempt_id, adapter_name, "
			+ "adapter_digest, profile_digest, created_at) VALUES (?, ?, ?, ?, ?)")
			.run("a1", "scripted", digest(1), digest(2), "2026-08-22");
		const observe = (incarnation, sourceSeq, managerSeq, what) =>
			db.prepare("INSERT INTO observations (runtime_attempt_id, "
				+ "incarnation, source_seq, runtime_id, observation_digest, "
				+ "manager_seq, observed_at) VALUES (?, ?, ?, ?, ?, ?, ?)")
				.run("a1", incarnation, sourceSeq, "runtime-1", digest(what),
				     managerSeq, "2026-08-22T18:00:00.000Z");
		observe("adapter-1", 1, 1, "running");
		// The RESTART: a new incarnation's first observation is admitted.
		observe("adapter-2", 1, 2, "running");
		assert.equal(db.prepare(
			"SELECT COUNT(*) AS n FROM observations").get().n, 2);
		// An exact duplicate within ONE incarnation still collides, which is
		// what makes replay answerable.
		assert.throws(() => observe("adapter-1", 1, 3, "running"),
			/UNIQUE|constraint/i);
		// A conflicting duplicate — same scope, different digest — collides
		// identically: the key is the SCOPE, and the digest is what a
		// replay/refuse decision reads afterwards.
		assert.throws(() => observe("adapter-1", 1, 4, "quiescent"),
			/UNIQUE|constraint/i);
		// And the manager's own sequence is unique per attempt whichever
		// incarnation produced it.
		assert.throws(() => observe("adapter-2", 2, 1, "quiescent"),
			/UNIQUE|constraint/i);
	} finally {
		store.close();
	}
});


test("W2929: a committed NULL result replays without running the act again", () => {
	// Re-review 2026-08-22 [P1]: `null` meant both "no operation row" and
	// "the committed result was JSON null", so an exact retry of a
	// null-returning operation looked new, ran the action a second time, and
	// only then hit the journal's primary key. Effectively-once cannot be
	// built on a value that also means absence.
	const store = open(storePath());
	try {
		const signature = managerSignature("output.retain", { attempt: "a1" });
		let ran = 0;
		const act = () => store.transact("op-null", "output.retain", signature,
			() => { ran += 1; return null; });
		assert.equal(act(), null);
		assert.equal(act(), null);
		assert.equal(ran, 1, "an exact retry of a null result ran the act again");
		assert.deepEqual(store.replay("op-null", signature),
		                 { found: true, value: null });
		// And a NEW identity is still distinguishable from that committed null.
		assert.deepEqual(store.replay("op-unseen", signature),
		                 { found: false, value: null });
	} finally {
		store.close();
	}
});


test("W2929: the journal records the bytes it validated, not a second read", () => {
	// Round-5 review [P1] names both halves. The reviewer's case proves the
	// guard SEES the serialized form; this one proves the row is not
	// reserialized afterwards — a `toJSON` that answers differently the
	// second time would otherwise commit whatever it liked.
	const store = open(storePath());
	try {
		let reads = 0;
		const result = { toJSON() {
			reads += 1;
			return reads === 1 ? { accepted: true } : { diagnostic: GOLDEN_BEARER };
		} };
		store.transact("op-once", "offer.accept",
			managerSignature("offer.accept", { offer: "offer-1" }),
			() => result);
		assert.equal(reads, 1, "the result was serialized more than once");
		assert.deepEqual(JSON.parse(store.operationRecord("op-once").result),
			{ accepted: true });
		// And the replay hands back those exact bytes rather than asking the
		// object again.
		assert.deepEqual(store.replay("op-once",
			managerSignature("offer.accept", { offer: "offer-1" })),
			{ found: true, value: { accepted: true } });
		assert.equal(reads, 1);
	} finally {
		store.close();
	}
});

test("W2929 review: the first result is the same durable copy a retry replays", () => {
	// The store boundary promises byte-stable results and says returned values
	// are copies, never caller-owned aliases. Once `toJSON` defines the durable
	// representation, the first answer must be that representation too — not
	// the action's mutable source object while a retry gets the parsed journal.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.accept", { offer: "offer-1" });
		const source = { transient: true, toJSON() {
			return { accepted: true, assignment_id: "assignment-1" };
		} };
		const first = store.transact("op-durable-copy", "offer.accept", signature,
			() => source);
		const retry = store.transact("op-durable-copy", "offer.accept", signature,
			() => { throw new Error("an exact retry performed the act"); });
		assert.deepEqual(first,
			{ accepted: true, assignment_id: "assignment-1" });
		assert.deepEqual(retry, first);
		assert.notStrictEqual(first, source,
			"the first result remained a caller-owned alias");
	} finally {
		store.close();
	}
});


test("W2929: the committed answer is one canonical value everywhere", () => {
	// Round-6 review [P1] names the first-call/retry split. These are the
	// two neighbouring properties: the answer is the SAME shape whether it
	// came from the action or the journal, and it is owned by nobody, so a
	// caller that mutates what it was handed cannot change what the next
	// caller is told.
	const store = open(storePath());
	try {
		const signature = managerSignature("offer.accept", { offer: "offer-1" });
		const source = { accepted: true, nested: { id: "assignment-1" } };
		const first = store.transact("op-owned", "offer.accept", signature,
			() => source);
		assert.notStrictEqual(first, source, "the answer aliased the action's object");
		assert.notStrictEqual(first.nested, source.nested,
			"a nested member of the answer aliased the action's object");
		first.nested.id = "tampered";
		const retry = store.transact("op-owned", "offer.accept", signature,
			() => { throw new Error("an exact retry performed the act"); });
		assert.deepEqual(retry, { accepted: true, nested: { id: "assignment-1" } },
			"mutating the first answer changed what the retry replays");
		// The journal is the authority for both, byte for byte.
		assert.deepEqual(JSON.parse(store.operationRecord("op-owned").result),
			retry);
	} finally {
		store.close();
	}
});

test("W2929: an action returning nothing answers null, once and for all", () => {
	// `undefined` has no JSON representation, so the durable answer is
	// `null` — and the first call must say so too rather than handing back
	// the `undefined` the action returned.
	const store = open(storePath());
	try {
		const signature = managerSignature("runtime.destroy", { attempt: "a1" });
		const first = store.transact("op-void", "runtime.destroy", signature,
			() => undefined);
		assert.equal(first, null);
		assert.equal(store.transact("op-void", "runtime.destroy", signature,
			() => { throw new Error("an exact retry performed the act"); }), null);
		assert.equal(store.operationRecord("op-void").result, "null");
	} finally {
		store.close();
	}
});
