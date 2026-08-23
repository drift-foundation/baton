// Deterministic W2929 first-slice review reproductions.
//
// Run from the repository root:
//   node work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-local-isolated-execution/findings/finding-v12-worker-manager-core/evidence/review-foundation-edges.mjs

import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { DatabaseSync } from "node:sqlite";

import {
	ContractError, canonicalBytes, digest, negotiate, validateEnvelope,
} from "../../../../../../../../../../v12/src/worker_manager/contracts.mjs";
import {
	ControlStore, managerSignature,
} from "../../../../../../../../../../v12/src/worker_manager/store.mjs";

const root = mkdtempSync(join(tmpdir(), "w2929-review-"));

function canonicalizationEdges() {
	const negative = canonicalBytes(-1).toString();
	const negativeZero = canonicalBytes(-0).toString();
	const loneSurrogate = canonicalBytes("\ud800").toString();
	console.log("canonicalization:", { negative, negativeZero, loneSurrogate });
	assert.equal(negative, "-1");
	assert.equal(negativeZero, "0");
	assert.equal(loneSurrogate, '"\\ud800"');
}

function negotiationEdges() {
	const agreed = negotiate({
		role: "runtime-adapter",
		supported_versions: [{ major: 1, minor: 0 }],
		capabilities: ["core.errors"],
		extensions: ["org.example.not-implemented/1"],
		// The frozen hello requires limits and runtime_profile_digest. Both
		// are deliberately absent here.
	});
	console.log("negotiation:", agreed);
	assert.deepEqual(agreed.extensions, ["org.example.not-implemented/1"]);
	assert.equal(Object.hasOwn(agreed, "effective_limits"), false);
}

function envelopeShapeEdge() {
	const body = {
		offer_id: "offer-1",
		runtime_attempt_id: "attempt-1",
		work_ref: {
			authority_uuid: "43c55d4b1234567890abcdef12345678",
			work_id: "43c55d4b-W2929",
		},
		decision: "decline",
		reason: "no capacity",
		claim_token: null,
	};
	const frame = {
		protocol: "baton.worker-control",
		version: { major: 1, minor: 0 },
		// A misspelled command is outside the closed schema. The semantic
		// validator treats every non-command as a reply and skips the signature.
		message_type: "commmand",
		kind: "offer.decide",
		operation: {
			operation_id: "operation-1",
			signature_digest: digest("stale signature"),
		},
		body_digest: digest(body),
		body,
	};
	validateEnvelope(frame);
	console.log("misspelled command with stale signature: accepted");
}

function observationIdentityEdge() {
	const store = new ControlStore(join(root, "observations.sqlite3"),
		{ incarnation: "manager-1" });
	try {
		store.db.prepare("INSERT INTO attempts (runtime_attempt_id, "
			+ "adapter_name, adapter_digest, profile_digest, created_at) "
			+ "VALUES (?, ?, ?, ?, ?)")
			.run("attempt-1", "scripted", digest(1), digest(2),
			     "2026-08-22T00:00:00.000Z");
		const insert = store.db.prepare("INSERT INTO observations "
			+ "(runtime_attempt_id, source_seq, incarnation, runtime_id, "
			+ "observation_digest, manager_seq, observed_at) "
			+ "VALUES (?, ?, ?, ?, ?, ?, ?)");
		insert.run("attempt-1", 1, "adapter-incarnation-1", "runtime-1",
		           digest({ state: "running" }), 1,
		           "2026-08-22T00:00:01.000Z");
		let collision;
		try {
			// source_seq is scoped to an adapter incarnation, so a fresh
			// incarnation may legitimately begin again at 1.
			insert.run("attempt-1", 1, "adapter-incarnation-2", "runtime-1",
			           digest({ state: "quiescent" }), 2,
			           "2026-08-22T00:00:02.000Z");
		} catch (error) {
			collision = error;
		}
		console.log("observation restart:", collision?.message);
		assert.match(collision?.message ?? "", /UNIQUE constraint failed/);
	} finally {
		store.close();
	}
}

function operationJournalEdges() {
	const store = new ControlStore(join(root, "operations.sqlite3"),
		{ incarnation: "manager-1" });
	try {
		const signature = managerSignature("output.retain", { result: "r1" });
		let first;
		try {
			store.transact("operation-1", "output.retain", signature, () => {
				const refusal = new ContractError("policy", "retention",
					"retention policy refused this result");
				refusal.durable = true;
				throw refusal;
			});
		} catch (error) {
			first = error;
		}
		let replay;
		try {
			store.replay("operation-1", signature);
		} catch (error) {
			replay = error;
		}
		const record = store.operationRecord("operation-1");
		console.log("durable refusal:", {
			first: [first.category, first.code],
			replay: [replay.category, replay.code],
			settled_at: record.settled_at,
		});
		assert.deepEqual([first.category, first.code], ["policy", "retention"]);
		assert.deepEqual([replay.category, replay.code],
		                 ["refused", "precondition"]);
		assert.equal(record.settled_at, "1970-01-01T00:00:00.000Z");
	} finally {
		store.close();
	}
}

function incompatibleSchemaEdge() {
	const path = join(root, "future.sqlite3");
	const future = new DatabaseSync(path);
	future.exec("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL) "
		+ "STRICT; INSERT INTO meta VALUES ('schema_version', '99')");
	future.close();
	assert.throws(() => new ControlStore(path, { incarnation: "manager-1" }),
	              /schema 99/);
	const inspected = new DatabaseSync(path);
	try {
		const tables = inspected.prepare(
			"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
			.all().map(({ name }) => name);
		console.log("future-schema tables after refused open:", tables);
		assert.ok(tables.includes("offers"));
	} finally {
		inspected.close();
	}
}

try {
	canonicalizationEdges();
	negotiationEdges();
	envelopeShapeEdge();
	observationIdentityEdge();
	operationJournalEdges();
	incompatibleSchemaEdge();
} finally {
	rmSync(root, { recursive: true, force: true });
}
