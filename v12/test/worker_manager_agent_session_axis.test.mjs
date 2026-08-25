// W2929 item 4, sixth slice: the agent-session observation axis.
//
// A transition table is the kind of thing that looks tested when three of its
// edges are driven, so this drives ALL of them — every ordered pair of the
// nine states, in both directions, against the frozen model's own literal.

import test, { after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ownedTemp, removeOwnedRoots } from "./owned_roots.mjs";
import { ContractError, digest } from "../src/worker_manager/contracts.mjs";
import { ControlStore } from "../src/worker_manager/store.mjs";
import { recordAttempt } from "../src/worker_manager/attempts.mjs";
import { AGENT_SESSION_SCHEMA_PATH }
	from "../src/worker_manager/agent_profile.mjs";
import { ALLOWED_SESSION_SUCCESSORS, SESSION_STATES,
         TERMINAL_SESSION_STATES, observeAgentSessionState,
         permitsSessionTransition, satisfiesRuntimeQuiescenceGate }
	from "../src/worker_manager/agent_session_axis.mjs";

after(removeOwnedRoots);

const UUID = "43c55d4b00ee85c84ae4ed134de36df5";
const WORK = "43c55d4b-W1439";
const ATTEMPT = "attempt-1";
const NOW = "2026-08-22T12:00:00.000Z";
const REF = { runtimeAttemptId: ATTEMPT, posture: "execution",
              sessionEpoch: 1 };

const HERE = dirname(fileURLToPath(import.meta.url));
const MODEL = readFileSync(join(HERE, "..", "..", "work", "records", "2026",
	"08", "finding-v12-isolated-agent-workers", "findings",
	"finding-v12-worker-contract", "findings", "finding-acp-agent-boundary",
	"evidence", "acp_boundary_model.py")).toString("utf8");

/** The frozen model's own successor table, parsed rather than retyped. */
function modelSuccessors() {
	const at = MODEL.indexOf("ALLOWED_SESSION_SUCCESSORS = {");
	assert.notEqual(at, -1, "the frozen model has no successor table");
	const body = MODEL.slice(at, MODEL.indexOf("\n}", at));
	const table = {};
	for (const line of body.split("\n").slice(1)) {
		const row = line.match(/^\s*"([a-z-]+)":\s*(\{[^}]*\}|set\(\))/);
		if (row === null) continue;
		table[row[1]] = [...row[2].matchAll(/"([a-z-]+)"/g)]
			.map((match) => match[1]).sort();
	}
	return table;
}

function open() {
	return new ControlStore(join(ownedTemp("v12-manager-"), "control.sqlite3"),
		{ incarnation: "manager-1", clock: () => NOW });
}

function withSession(store, state = "not-started") {
	recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
		adapterDigest: digest("adapter"), profileDigest: digest("profile") });
	store.db.prepare(
		"INSERT INTO agent_sessions (runtime_attempt_id, posture, "
		+ "session_epoch, profile_digest, pinned_policy, work_id, "
		+ "authority_uuid, state, opened_at) "
		+ "VALUES (?, 'execution', 1, ?, ?, ?, ?, ?, ?)")
		.run(ATTEMPT, digest("profile"), digest("policy"), WORK, UUID, state,
		     NOW);
	return REF;
}

function storedState(store) {
	return store.db.prepare("SELECT state FROM agent_sessions").get().state;
}

// -- the table -----------------------------------------------------------------

test("W2929: the nine states are the frozen vocabulary's nine", () => {
	const schema = JSON.parse(
		readFileSync(AGENT_SESSION_SCHEMA_PATH).toString("utf8"));
	assert.deepEqual([...SESSION_STATES].sort(),
		[...schema.$defs.sessionState.enum].sort());
	assert.equal(SESSION_STATES.length, 9);
	// Every state has a successor row, and every named successor is a state.
	assert.deepEqual(Object.keys(ALLOWED_SESSION_SUCCESSORS).sort(),
		[...SESSION_STATES].sort());
	for (const [from, successors] of
			Object.entries(ALLOWED_SESSION_SUCCESSORS)) {
		for (const to of successors) {
			assert.equal(SESSION_STATES.includes(to), true, `${from} -> ${to}`);
		}
	}
});

test("W2929: the successor table is the frozen model's, edge for edge", () => {
	// Parsed out of the design model rather than retyped, because a table I
	// transcribe twice is a table I can get wrong twice in the same
	// direction — and a transition table is where that is least visible.
	const model = modelSuccessors();
	assert.equal(Object.keys(model).length, 9, "the model table did not parse");
	for (const state of SESSION_STATES) {
		assert.deepEqual([...ALLOWED_SESSION_SUCCESSORS[state]].sort(),
			model[state], state);
	}
});

test("W2929: `unknown` and `closed` are the terminal two, and unknown stays",
	() => {
		assert.deepEqual([...TERMINAL_SESSION_STATES], ["unknown", "closed"]);
		// The one edge the whole axis exists to forbid: `unknown` means no
		// terminal fact was observed, so promoting it to `closed` would
		// record knowledge nobody acquired.
		assert.equal(permitsSessionTransition("unknown", "closed"), false);
		assert.equal(permitsSessionTransition("closed", "unknown"), false);
		// Every state can reach `unknown` except the terminal two AND
		// `agent-quiescent` — which is the interesting exception and was my
		// own first assertion's mistake. `agent-quiescent` means a terminal
		// turn fact WAS observed after cancellation was ordered, so the
		// ending is known; moving to `unknown` there would be a regression in
		// knowledge, not the honest absence of it. The transport dying at any
		// other point is what the rest of the column is for.
		// `unknown` itself is absent from this list, because re-observing it
		// is a self-observation and those are always permitted — the axis
		// does not move, and a duplicate is not a regression.
		assert.deepEqual(SESSION_STATES.filter(
			(state) => !permitsSessionTransition(state, "unknown")),
			["agent-quiescent", "closed"]);
	});

test("W2929: EVERY ordered pair of the nine is decided, both ways", () => {
	// Eighty-one pairs. A transition table driven at three edges is a table
	// nobody has checked, and the interesting edges are the ones a spine
	// diagram does not draw.
	let permitted = 0;
	let refused = 0;
	for (const from of SESSION_STATES) {
		for (const to of SESSION_STATES) {
			const expected = from === to
				|| ALLOWED_SESSION_SUCCESSORS[from].includes(to);
			assert.equal(permitsSessionTransition(from, to), expected,
				`${from} -> ${to}`);
			if (expected) permitted += 1; else refused += 1;
		}
	}
	assert.equal(permitted + refused, 81);
	// Nine self-observations plus the table's edges, so the split is a fact
	// rather than whatever the loop happened to count.
	const edges = Object.values(ALLOWED_SESSION_SUCCESSORS)
		.reduce((total, successors) => total + successors.length, 0);
	assert.equal(permitted, 9 + edges);
});

test("W2929: a state outside the nine is refused rather than answered", () => {
	for (const state of ["running", "READY", "", null, undefined, 7]) {
		assert.throws(() => permitsSessionTransition("ready", state),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema", String(state));
		assert.throws(() => permitsSessionTransition(state, "ready"),
			(error) => error instanceof ContractError
				&& error.code === "schema", String(state));
		// §7.4's gate validates its question too: answering `false` to a
		// malformed question is how a caller concludes it asked a good one.
		assert.throws(() => satisfiesRuntimeQuiescenceGate(state),
			(error) => error instanceof ContractError
				&& error.code === "schema", String(state));
	}
});

// -- the durable axis --------------------------------------------------------

test("W2929: the durable axis moves along the table and records it", () => {
	const store = open();
	try {
		withSession(store);
		// The spine, one edge at a time, and the row follows.
		for (const [from, to] of [["not-started", "initializing"],
		                          ["initializing", "ready"],
		                          ["ready", "prompting"],
		                          ["prompting", "turn-ended"],
		                          // A SECOND supervised turn in one epoch,
		                          // which is the edge the turn slice's
		                          // allocated identity exists for.
		                          ["turn-ended", "prompting"],
		                          ["prompting", "cancel-requested"],
		                          ["cancel-requested", "agent-quiescent"],
		                          ["agent-quiescent", "closed"]]) {
			assert.equal(storedState(store), from, `${from} -> ${to}`);
			assert.deepEqual(observeAgentSessionState(store, REF, to),
				{ state: to, moved: true }, `${from} -> ${to}`);
			assert.equal(storedState(store), to);
		}
	} finally {
		store.close();
	}
});

test("W2929: observing the SAME state again answers rather than refuses", () => {
	const store = open();
	try {
		withSession(store, "prompting");
		// A retransmitted observation is the same observation. Refusing it
		// would make an ordinary duplicate look like a regression, which is
		// the reading the event slice already rejected for frames.
		assert.deepEqual(observeAgentSessionState(store, REF, "prompting"),
			{ state: "prompting", moved: false });
		assert.equal(storedState(store), "prompting");
	} finally {
		store.close();
	}
});

test("W2929 review: a state observation binds the full session identity",
	() => {
		const store = open();
		try {
			withSession(store, "ready");
			store.db.prepare("UPDATE agent_sessions SET provider_session_id = ?")
				.run("provider-session-a");
			// The provider id is diagnostic and authorizes nothing, but §3.1
			// makes it the fourth component of the reference that LABELS this
			// evidence. A different or missing label cannot move this row.
			for (const providerSessionId of ["provider-session-b", null,
			                                  undefined]) {
				for (const observed of ["ready", "prompting"]) {
					assert.throws(() => observeAgentSessionState(store,
						{ ...REF, providerSessionId }, observed),
						(error) => error instanceof ContractError
							&& error.category === "runtime-observation"
							&& error.code === "identity-mismatch",
						`${String(providerSessionId)} / ${observed}`);
				}
				assert.equal(storedState(store), "ready");
			}
			assert.deepEqual(observeAgentSessionState(store,
				{ ...REF, providerSessionId: "provider-session-a" }, "prompting"),
				{ state: "prompting", moved: true });
		} finally {
			store.close();
		}
	});

test("W2929 review: the axis proves its session reference before lookup",
	() => {
		for (const [what, ref] of [
			["absent", null],
			["empty attempt", { ...REF, runtimeAttemptId: "" }],
			["foreign posture", { ...REF, posture: "review" }],
			["zero epoch", { ...REF, sessionEpoch: 0 }],
			["numeric provider id", { ...REF, providerSessionId: 7 }],
			["empty provider id", { ...REF, providerSessionId: "" }],
		]) {
			const store = open();
			try {
				withSession(store, "ready");
				assert.throws(() => observeAgentSessionState(store, ref, "prompting"),
					(error) => error instanceof ContractError
						&& error.category === "integrity"
						&& error.code === "schema", what);
				assert.equal(storedState(store), "ready", what);
			} finally {
				store.close();
			}
		}
	});

test("W2929 correction: the label is bound BEFORE the self-observation answer",
	() => {
		// The half a move-only check would miss. Affirming that provider
		// session B's axis reads `prompting` is a claim about B, and
		// answering it from A's row is the same mistake as moving A's row —
		// so the reviewer's case drives it and this one states why, over
		// every state the row can hold.
		for (const held of SESSION_STATES) {
			const store = open();
			try {
				withSession(store, held);
				store.db.prepare(
					"UPDATE agent_sessions SET provider_session_id = ?")
					.run("provider-session-a");
				// The SAME state, so nothing would move even if the binding
				// were skipped; only the identity is wrong.
				assert.throws(() => observeAgentSessionState(store,
					{ ...REF, providerSessionId: "provider-session-b" }, held),
					(error) => error instanceof ContractError
						&& error.category === "runtime-observation"
						&& error.code === "identity-mismatch", held);
				// And the agreeing label gets the ordinary no-op answer.
				assert.deepEqual(observeAgentSessionState(store,
					{ ...REF, providerSessionId: "provider-session-a" }, held),
					{ state: held, moved: false }, held);
			} finally {
				store.close();
			}
		}
	});

test("W2929 correction: an unlabelled session is bound by its absence", () => {
	const store = open();
	try {
		withSession(store, "ready");
		// The fixture's session holds NULL, so a reference naming any
		// provider id disagrees with it. Saying nothing is agreement here and
		// saying something is not — the mirror of the case above.
		assert.throws(() => observeAgentSessionState(store,
			{ ...REF, providerSessionId: "provider-session-a" }, "prompting"),
			(error) => error instanceof ContractError
				&& error.category === "runtime-observation"
				&& error.code === "identity-mismatch");
		assert.equal(storedState(store), "ready");
		assert.deepEqual(observeAgentSessionState(store,
			{ ...REF, providerSessionId: null }, "prompting"),
			{ state: "prompting", moved: true });
	} finally {
		store.close();
	}
});

test("W2929: a regression refuses and the durable state does not move", () => {
	const store = open();
	try {
		withSession(store, "turn-ended");
		for (const backwards of ["not-started", "initializing", "ready"]) {
			assert.throws(
				() => observeAgentSessionState(store, REF, backwards),
				(error) => error instanceof ContractError
					&& error.category === "runtime-observation"
					&& error.code === "state-regression", backwards);
			assert.equal(storedState(store), "turn-ended");
		}
	} finally {
		store.close();
	}
});

test("W2929: a terminal epoch admits no further observation at all", () => {
	for (const terminal of TERMINAL_SESSION_STATES) {
		const store = open();
		try {
			withSession(store, terminal);
			for (const state of SESSION_STATES) {
				if (state === terminal) {
					assert.deepEqual(
						observeAgentSessionState(store, REF, state),
						{ state, moved: false });
					continue;
				}
				assert.throws(
					() => observeAgentSessionState(store, REF, state),
					(error) => error instanceof ContractError
						&& error.category === "runtime-observation"
						&& error.code === "state-regression",
					`${terminal} -> ${state}`);
			}
			assert.equal(storedState(store), terminal);
		} finally {
			store.close();
		}
	}
});

test("W2929: an axis belongs to a session", () => {
	const store = open();
	try {
		recordAttempt(store, { attemptId: ATTEMPT, adapterName: "scripted",
			adapterDigest: digest("adapter"),
			profileDigest: digest("profile") });
		assert.throws(() => observeAgentSessionState(store, REF, "ready"),
			(error) => error instanceof ContractError
				&& error.category === "refused"
				&& error.code === "precondition");
	} finally {
		store.close();
	}
});

test("W2929: a stored state outside the nine decides nothing", () => {
	const store = open();
	try {
		withSession(store);
		// A row edited to carry a state this contract never had would index
		// into the table and read `undefined`, so it is proved before it is
		// used rather than after.
		store.db.prepare("UPDATE agent_sessions SET state = 'invented'").run();
		assert.throws(() => observeAgentSessionState(store, REF, "ready"),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		// AND OBSERVING THAT SAME INVENTED STATE. This is the input the
		// self-observation shortcut would otherwise answer `moved: false` to
		// without either value being proved — the one path where the two
		// validations do not cover for each other, and it was a gap in this
		// case rather than in the code, found by a mutation that reported
		// zero witnesses.
		assert.throws(() => observeAgentSessionState(store, REF, "invented"),
			(error) => error instanceof ContractError
				&& error.category === "integrity"
				&& error.code === "schema");
		assert.equal(storedState(store), "invented");
	} finally {
		store.close();
	}
});

// -- §7.4 --------------------------------------------------------------------

test("W2929: NO agent-session state satisfies runtime quiescence", () => {
	// The one function here that always answers false, driven over all nine.
	// `agent-quiescent` is the state most likely to be mistaken for the gate,
	// which is why §7.4 is titled the way it is: a finished conversation says
	// nothing about whether the runtime holding the generation is gone.
	for (const state of SESSION_STATES) {
		assert.equal(satisfiesRuntimeQuiescenceGate(state), false, state);
	}
});
