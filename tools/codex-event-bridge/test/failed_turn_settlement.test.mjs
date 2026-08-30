// W4303: a managed turn that fails HOLDING a claim is settled, not
// reported idle.
//
// `work/records/2026/08/finding-managed-turn-failure-orphans-claim/`.
//
// The incident: the dispatcher delivered W2907 to `baton.codex`, the
// agent claimed it atomically at 07:17:03Z, and the turn terminated as
// `failed` at 07:17:04Z without reviewing anything and without passing
// or releasing the Work. `#turnCompleted` published `idle`, cleared the
// turn and drained on. Five hours later canonical state still read
// `active` with that Handler while the runtime projection reported the
// same context idle — and because a participant holds at most one claim,
// two later review wakes could not be claimed at all. W2928 was never
// reviewed and its dependent W2929 never moved.
//
// The correction, in one shared settlement path used by every completion
// ordering: re-read the participant's canonical claim slot. If the exact
// delivered claim OR a different secondary claim survives, fence the target,
// publish
// `failed(internal)` rather than `idle`, file one durable Work-correlated
// incident, and RETAIN the queued readiness so later work is visibly
// blocked on participant capacity rather than silently spent against a
// lane that cannot accept it.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { actionEvent, claimedFirst } from "../src/codex_baton_bridge.mjs";
import { quarantineKey } from "../src/quarantine_store.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";
import { FIXTURE_POLICY } from "./stale_episode.test.mjs";

const quiet = { info() {}, warn() {}, error() {}, debug() {} };
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";
const WORK = "7ba67cb8-W2907";
const EPISODE = 2907;
const KEY = `work:${WORK}:${EPISODE}:g1`;

class FakeClient extends EventEmitter {
	constructor() {
		super();
		this.connected = true;
		this.starts = [];
		this.nextTurn = null;
		this.resumeStatus = { type: "idle" };
		this.resumeTurns = [];
		// Read separately from the resume snapshot on purpose: the two
		// disagree exactly when `#reconcileAmbiguous` matters, because
		// resume did not resolve the ambiguous delivery and a later
		// `readThread` does.
		this.threadTurns = [];
	}

	async connectAndInitialize() {
		this.connected = true;
		this.emit("connected", {});
	}

	async startTurn(threadId, text, clientId) {
		this.starts.push({ threadId, text, clientId });
		const turn = this.nextTurn
			? await this.nextTurn(this.starts.length)
			: { id: `turn-${this.starts.length}`, status: "inProgress" };
		return turn;
	}

	async resume(threadId) {
		return { thread: { id: threadId, status: this.resumeStatus,
			turns: this.resumeTurns } };
	}

	async readThread(threadId) {
		return { id: threadId, status: { type: "idle" }, turns: this.threadTurns };
	}

	disconnect() {
		const wasConnected = this.connected;
		this.connected = false;
		if (wasConnected) this.emit("disconnected");
	}
}

function config(quarantineDir) {
	return validateConfig({
		servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
		targets: {
			codex: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.codex", role: "rview",
					actionOwner: "baton.slaw" } },
		},
		roleInstructions: { binary: "/opt/baton/bin/baton",
			config: "/home/op/baton.json", execPolicyFile: FIXTURE_POLICY },
		eventSocket: "/tmp/codex-w4303-unused.sock",
		quarantineDir,
		reconnectMinMs: 1,
		reconnectMaxMs: 2,
	});
}

/** The producer's own event, so this suite cannot drift from the shape
 *  the dispatcher actually receives. */
function readinessEvent({ key = KEY, work = WORK, episode = EPISODE,
                          claimed = false, participant = "baton.codex",
                          correlated = true } = {}) {
	const envelope = { authority_uuid: UUID, participant,
		result: { actionable: [] } };
	const action = { kind: "work", action_key: key,
		...(correlated ? { work } : {}),
		local_id: work.split("-").pop(), title: "reconcile the orphan",
		phase: claimed ? "active" : "queued", claimed,
		...(correlated ? { episode_seq: episode } : {}),
		config_generation: 1 };
	return actionEvent(envelope, action, { target: "codex" });
}

/** One canonical `wait timeout=0` answer, scripted per call. */
function authority(answers) {
	const calls = [];
	const queue = [...answers];
	return {
		calls,
		revalidate: async (file, args) => {
			calls.push({ file, args });
			const next = queue.length > 1 ? queue.shift() : queue[0];
			if (next instanceof Error) throw next;
			if (typeof next === "string") return { stdout: next };
			return { stdout: JSON.stringify(canonical(next)) };
		},
	};
}

/** The whole canonical envelope.
 *
 *  W11910 review [P1]: the dispatcher's revalidation applies the same typed
 *  v11 contract both readiness producers apply to this command's output, so a
 *  fixture carrying only an actionable array is a reply the real authority
 *  never emits — and a suite built on one would be proving the behaviour of
 *  code that does not run. */
function canonical(actionable, participant = "baton.codex") {
	return { protocol_version: 11, projection_version: "12.4",
		authority_uuid: UUID, participant, snapshot_seq: 1,
		result: { timed_out: false, actionable } };
}

function entry(work, episode, claimed) {
	return { kind: "work", action_key: `work:${work}:${episode}:g1`,
		work, episode_seq: episode, config_generation: 1, claimed };
}

const W2928 = "7ba67cb8-W2928";
const W2929 = "7ba67cb8-W2929";
const OFFERED = [entry(WORK, EPISODE, false)];
const HELD = [entry(WORK, EPISODE, true)];
const SECONDARY_EPISODE = 2928;
const SECONDARY_KEY = `work:${W2928}:${SECONDARY_EPISODE}:g1`;
const SECONDARY_HELD = [entry(W2928, SECONDARY_EPISODE, true)];

function bridge({ revalidate, quarantineDir = freshQuarantineDir(),
                  runtime = {} } = {}) {
	const fake = new FakeClient();
	const published = [];
	const incidents = [];
	const dispatcher = new EventBridge({
		config: config(quarantineDir), logger: quiet,
		clientFactory: () => fake,
		runtimeFactory: () => ({
			incarnation: "run-1",
			async start() {},
			async state(name, detail) { published.push([name, detail]); },
			async incident(entry) { incidents.push(entry); return true; },
			async facts() { return true; },
			async end() {},
			// A case that needs a runner which REFUSES or throws overrides
			// exactly the method it is about; everything else stays the
			// shared honest double.
			...runtime,
		}),
		revalidate,
	});
	return { dispatcher, fake, published, incidents, quarantineDir };
}

async function settle(times = 8) {
	for (let index = 0; index < times; index += 1) {
		await new Promise((resolve) => setImmediate(resolve));
	}
}

async function ready(dispatcher, fake) {
	await dispatcher.start({ listen: false });
	fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
	await settle();
}

/** Deliver one readiness event and end its turn with `status`. */
async function deliverThenEnd(dispatcher, fake, status, event = readinessEvent()) {
	dispatcher.enqueue(event);
	await settle();
	const turn = { id: `turn-${fake.starts.length}`, status };
	fake.emit("turnCompleted", { threadId: "thread-a", turn });
	await settle();
	return turn;
}

// -- the defect --------------------------------------------------------------

test("a turn that fails holding the claim never reports the runner idle",
	async () => {
		// The exact W2907 sequence. `answering` returns the delivered
		// episode STILL CLAIMED, which is the canonical contradiction the
		// runtime projection could not see.
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			assert.equal(published.some(([name]) => name === "idle"), false,
				"an orphaned claim was published as an idle runner");
			const failure = published.findLast(([name]) => name === "failed");
			assert.ok(failure, "no failed state was published at all");
			assert.equal(failure[1].cause, "internal");
			assert.equal(incidents.length, 1);
			assert.equal(incidents[0].cause, "internal");
			assert.equal(incidents[0].category, "other");
			assert.equal(incidents[0].work, WORK);
			assert.equal(incidents[0].episode, EPISODE);
			assert.equal(incidents[0].actionKey, KEY);
		} finally {
			await dispatcher.stop();
		}
	});

test("a turn that fails BEFORE the claim leaves the target deliverable",
	async () => {
		// The other half of the acceptance boundary. Nothing was claimed,
		// so nothing was orphaned: the runner is idle and the next event
		// drains exactly as it did before.
		const answer = authority([OFFERED]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			assert.equal(published.some(([name]) => name === "idle"), true);
			assert.equal(incidents.length, 0);
			assert.equal(
				dispatcher.statusSnapshot().targets.codex.deliverable, true);
		} finally {
			await dispatcher.stop();
		}
	});

test("W39868: a failed turn fences the participant's secondary claim",
	async () => {
		// The exact W39770/W39357 shape: the delivered action was released,
		// readiness stayed armed inside the same managed turn, and the
		// participant claimed another Work before that turn failed. The claim
		// slot is occupied even though the original correlation is gone.
		const answer = authority([OFFERED, SECONDARY_HELD]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			assert.equal(published.some(([name]) => name === "idle"), false,
				"a secondary live claim was published as a free runner");
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.equal(row.deliverable, false);
			assert.deepEqual({ work: row.orphan.work, episode: row.orphan.episode,
				actionKey: row.orphan.actionKey,
				correlation: row.orphan.correlation },
				{ work: W2928, episode: SECONDARY_EPISODE,
					actionKey: SECONDARY_KEY, correlation: "secondary" });
			assert.equal(incidents.length, 1);
			assert.equal(incidents[0].work, W2928);
			assert.equal(incidents[0].episode, SECONDARY_EPISODE);
			assert.equal(incidents[0].actionKey, SECONDARY_KEY);
			assert.match(incidents[0].detail, /secondary claim/);
			dispatcher.enqueue(readinessEvent({ key: `work:${W2929}:3:g1`,
				work: W2929, episode: 3 }));
			await settle();
			assert.equal(fake.starts.length, 1,
				"queued readiness drained into the secondary claim's occupied lane");
			assert.equal(dispatcher.globalQueueDepth, 1,
				"queued readiness was dropped instead of retained");
		} finally {
			await dispatcher.stop();
		}
	});

test("a turn that COMPLETES is never reconciled at all", async () => {
	// `completed` is the one success terminal, and settling it would spend
	// a canonical read on every ordinary turn this dispatcher runs.
	const answer = authority([OFFERED, HELD]);
	const { dispatcher, fake, published } =
		bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		// Counted AFTER the delivery, whose own W1224 revalidation is a
		// different read with a different purpose.
		const before = answer.calls.length;
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: `turn-${fake.starts.length}`, status: "completed" } });
		await settle();
		assert.equal(answer.calls.length, before,
			"a successful turn was reconciled against the authority");
		assert.equal(published.some(([name]) => name === "idle"), true);
	} finally {
		await dispatcher.stop();
	}
});

test("a canonical read that fails or is malformed fences rather than drains",
	async () => {
		for (const answer of [authority([OFFERED, new Error("baton unreachable")]),
		                      authority([OFFERED, "{\"result\":{}}"]),
		                      authority([OFFERED, "not json at all"])]) {
			const { dispatcher, fake, published, incidents } =
				bridge({ revalidate: answer.revalidate });
			try {
				await ready(dispatcher, fake);
				await deliverThenEnd(dispatcher, fake, "failed");
				assert.equal(published.some(([name]) => name === "idle"), false,
					"an unreadable reconciliation was read as a free lane");
				assert.equal(incidents.length, 1);
				const row = dispatcher.statusSnapshot().targets.codex;
				assert.equal(row.deliverable, false);
				assert.equal(row.orphan.correlation, "unreadable");
			} finally {
				await dispatcher.stop();
			}
		}
	});

test("later readiness is retained, never delivered into the blocked lane",
	async () => {
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			const delivered = fake.starts.length;
			dispatcher.enqueue(readinessEvent({ key: `work:${W2928}:9:g1`,
				work: W2928, episode: 9 }));
			await settle();
			assert.equal(fake.starts.length, delivered,
				"a model turn was spent on Work the occupied lane cannot claim");
			assert.equal(dispatcher.globalQueueDepth, 1,
				"the retained wake was dropped instead of held");
		} finally {
			await dispatcher.stop();
		}
	});

// -- the completion-before-start-response ordering ----------------------------

test("a completion that beats its own turn/start settles on the same path",
	async () => {
		// The regressed ordering. `turn/completed` arrives while
		// `turn/start` is still in flight, so `#turnCompleted` cannot tell
		// it from an interactive turn — and used to publish `idle` for it
		// unconditionally. The `idle` is HELD until the binding decides,
		// and `#drain` then runs the same settlement.
		const answer = authority([OFFERED, SECONDARY_HELD]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			fake.nextTurn = async (index) => {
				const turn = { id: `turn-${index}`, status: "inProgress" };
				// The completion lands BEFORE this call returns.
				fake.emit("turnCompleted",
					{ threadId: "thread-a", turn: { ...turn, status: "failed" } });
				return turn;
			};
			dispatcher.enqueue(readinessEvent());
			await settle();
			assert.equal(published.some(([name]) => name === "idle"), false,
				"the early completion published idle over an orphaned claim");
			assert.equal(incidents.length, 1);
			assert.equal(incidents[0].work, W2928);
			assert.equal(incidents[0].episode, SECONDARY_EPISODE);
		} finally {
			await dispatcher.stop();
		}
	});

test("a failed turn with a secondary claim discovered during reconnect is settled", async () => {
	// A transport drop can hide `turn/completed`. The resume snapshot is
	// then the first and only place the dispatcher observes the terminal
	// failure. Clearing `activeTurn` there without the shared settlement
	// recreates W4303 exactly: canonical state still has the claim, while
	// the dispatcher considers the target deliverable.
	const answer = authority([OFFERED, SECONDARY_HELD]);
	const { dispatcher, fake, incidents } =
		bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		assert.equal(fake.starts.length, 1);
		fake.resumeStatus = { type: "idle" };
		fake.resumeTurns = [{ id: "turn-1", status: "failed" }];
		fake.disconnect();
		await new Promise((resolve) => setTimeout(resolve, 30));
		await settle();
		const row = dispatcher.statusSnapshot().targets.codex;
		assert.deepEqual({ deliverable: row.deliverable,
			orphan: row.orphan?.work ?? null, incidents: incidents.length },
			{ deliverable: false, orphan: W2928, incidents: 1 },
			"resume cleared a failed turn without reconciling its surviving claim");
	} finally {
		await dispatcher.stop();
	}
});

/** Deliver one event, then reconnect with a scripted resume snapshot.
 *  The disconnect is what hides `turn/completed`, which is the whole
 *  reason resume is the first observation of the terminal turn. */
async function deliverThenReconnect(dispatcher, fake, { status, turns }) {
	dispatcher.enqueue(readinessEvent());
	await settle();
	fake.resumeStatus = status;
	fake.resumeTurns = turns;
	fake.disconnect();
	await new Promise((resolve) => setTimeout(resolve, 30));
	await settle();
	return dispatcher.statusSnapshot().targets.codex;
}

test("a SUCCESSFUL turn discovered during reconnect is not fenced", async () => {
	// The other half of the review's boundary. `completed` is the one
	// success terminal, so resume settlement must return without reading
	// the authority at all — otherwise every reconnect after an ordinary
	// turn would spend a canonical read and, worse, could fence a target
	// on a claim the completed turn is legitimately still holding.
	const answer = authority([OFFERED]);
	const { dispatcher, fake, incidents } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		// AFTER the delivery, which spends its own episode check.
		const before = answer.calls.length;
		fake.resumeStatus = { type: "idle" };
		fake.resumeTurns = [{ id: "turn-1", status: "completed" }];
		fake.disconnect();
		await new Promise((resolve) => setTimeout(resolve, 30));
		await settle();
		const row = dispatcher.statusSnapshot().targets.codex;
		assert.equal(row.deliverable, true, "a completed turn fenced its target");
		assert.equal(row.orphan ?? null, null);
		assert.equal(incidents.length, 0);
		assert.equal(answer.calls.length, before,
			"a completed turn was reconciled against the authority anyway");
	} finally {
		await dispatcher.stop();
	}
});

test("a failed turn found on reconnect whose claim is GONE is not fenced",
	async () => {
		// The ordinary case, and the one that says this settlement is
		// narrow: the turn failed after passing the Work on, so the
		// authority no longer records the claim and nothing was orphaned.
		const answer = authority([OFFERED, []]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			const row = await deliverThenReconnect(dispatcher, fake,
				{ status: { type: "idle" }, turns: [{ id: "turn-1", status: "failed" }] });
			assert.equal(row.deliverable, true,
				"a failure that orphaned nothing fenced its target");
			assert.equal(incidents.length, 0);
		} finally {
			await dispatcher.stop();
		}
	});

test("a late turn/completed after resume settlement files nothing twice",
	async () => {
		// Idempotence, which the review names explicitly. The notification
		// the transport swallowed can still arrive after reconnect; the
		// fence is already durable, so the second settlement must not
		// re-mint it, re-report `failed`, or file the incident again.
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenReconnect(dispatcher, fake,
				{ status: { type: "idle" }, turns: [{ id: "turn-1", status: "failed" }] });
			assert.equal(incidents.length, 1);
			const failures = published.filter(([name]) => name === "failed").length;
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-1", status: "failed" } });
			await settle();
			assert.equal(incidents.length, 1, "the late notification filed a second incident");
			assert.equal(published.filter(([name]) => name === "failed").length,
				failures, "the late notification re-reported the same failure");
			assert.equal(published.some(([name]) => name === "idle"), false,
				"the late notification published idle over the fence");
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.equal(row.deliverable, false);
			assert.equal(row.orphan.work, WORK);
		} finally {
			await dispatcher.stop();
		}
	});

test("a reconnect settlement racing late turn/completed files one incident",
	async () => {
		// The sequential late-notification case above starts only after the
		// resume settlement has acknowledged its incident. A notification can
		// instead arrive while that settlement is awaiting its canonical read.
		// Both observers then reach the shared settlement concurrently, so the
		// one-incident guarantee needs an in-flight fence, not only the durable
		// acknowledgement written after publication returns.
		let calls = 0;
		let releaseRead;
		let firstRead;
		let secondRead;
		const held = new Promise((resolve) => { releaseRead = resolve; });
		const firstEntered = new Promise((resolve) => { firstRead = resolve; });
		const secondEntered = new Promise((resolve) => { secondRead = resolve; });
		const revalidate = async () => {
			calls += 1;
			if (calls === 1) return { stdout: JSON.stringify(canonical(OFFERED)) };
			if (calls === 2) firstRead();
			if (calls === 3) secondRead();
			await held;
			return { stdout: JSON.stringify(canonical(HELD)) };
		};
		const { dispatcher, fake, incidents } = bridge({ revalidate });
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent());
			await settle();
			fake.resumeStatus = { type: "idle" };
			fake.resumeTurns = [{ id: "turn-1", status: "failed" }];
			fake.disconnect();
			await firstEntered;
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-1", status: "failed" } });
			await secondEntered;
			releaseRead();
			await settle();
			assert.equal(incidents.length, 1,
				"concurrent settlement observers filed the same incident twice");
		} finally {
			releaseRead();
			await dispatcher.stop();
		}
	});

test("a FAILED first publication stays retryable for the next observer",
	async () => {
		// The other half of the review's requirement, and the half a shared
		// promise could quietly break: joining is only correct if a
		// publication that did NOT reach the authority leaves the fence
		// unacknowledged and the next observer free to try again.
		//
		// A runner that answers `false` has not filed anything, so the
		// durable acknowledgement must stay false and the in-flight handle
		// must not survive as a permanent "already filed".
		const answer = authority([OFFERED, HELD]);
		const attempts = [];
		const { dispatcher, fake, incidents } = bridge({
			revalidate: answer.revalidate,
			runtime: {
				async incident(entry) {
					attempts.push(entry);
					// The first publication fails; the second succeeds.
					return attempts.length > 1;
				},
			},
		});
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			assert.equal(attempts.length, 1);
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.equal(row.orphan.incidentFiled ?? false, false,
				"a publication the runner refused was acknowledged anyway");
			// A later observer retries rather than joining a dead handle.
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-1", status: "failed" } });
			await settle();
			assert.equal(attempts.length, 2,
				"the refused publication was never retried");
			assert.equal(
				dispatcher.statusSnapshot().targets.codex.orphan.incidentFiled,
				true);
			// And once acknowledged it files ONCE, however many observe it.
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-1", status: "failed" } });
			await settle();
			assert.equal(attempts.length, 2);
			assert.equal(incidents.length, 0, "the fixture counted for us");
		} finally {
			await dispatcher.stop();
		}
	});

test("a THROWING publication also stays retryable", async () => {
	// A runner that rejects is not a runner that filed. The in-flight
	// handle has to be cleared on the failure path too, or one transport
	// error would permanently convince this fence it had already published.
	const answer = authority([OFFERED, HELD]);
	const attempts = [];
	const { dispatcher, fake } = bridge({
		revalidate: answer.revalidate,
		runtime: {
			async incident(entry) {
				attempts.push(entry);
				if (attempts.length === 1) throw new Error("transport is down");
				return true;
			},
		},
	});
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "turn-1", status: "failed" } });
		await settle();
		assert.equal(attempts.length, 1);
		const row = dispatcher.statusSnapshot().targets.codex;
		assert.equal(row.orphan.incidentFiled ?? false, false);
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "turn-1", status: "failed" } });
		await settle();
		assert.equal(attempts.length, 2,
			"a rejected publication was never retried");
	} finally {
		await dispatcher.stop();
	}
});

test("a late acknowledgement cannot mark a successor orphan filed", async () => {
	// An incident publication belongs to the orphan object it captured. While
	// that publication is in flight, the authority can prove the first claim
	// gone, the retained queue can drain, and a later failed turn can create a
	// new orphan. Acknowledging through `state.orphan` would then mark the NEW
	// fence filed even though its own publication has not succeeded.
	const secondWork = W2928;
	const secondEpisode = 2928;
	const secondKey = `work:${secondWork}:${secondEpisode}:g1`;
	const answers = authority([
		OFFERED,
		HELD,
		[],
		[entry(secondWork, secondEpisode, false)],
		[entry(secondWork, secondEpisode, true)],
	]);
	let releaseFirst;
	let releaseSecond;
	let firstEntered;
	let secondEntered;
	const firstPublication = new Promise((resolve) => { releaseFirst = resolve; });
	const secondPublication = new Promise((resolve) => { releaseSecond = resolve; });
	const firstStarted = new Promise((resolve) => { firstEntered = resolve; });
	const secondStarted = new Promise((resolve) => { secondEntered = resolve; });
	let publications = 0;
	const { dispatcher, fake } = bridge({
		revalidate: answers.revalidate,
		runtime: {
			async incident() {
				publications += 1;
				if (publications === 1) {
					firstEntered();
					return firstPublication;
				}
				secondEntered();
				return secondPublication;
			},
		},
	});
	try {
		await ready(dispatcher, fake);
		dispatcher.enqueue(readinessEvent());
		await settle();
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "turn-1", status: "failed" } });
		await firstStarted;
		await new Promise((resolve) => setTimeout(resolve, 5));
		dispatcher.enqueue(readinessEvent({ key: secondKey, work: secondWork,
			episode: secondEpisode }));
		await settle();
		assert.equal(fake.starts.length, 2,
			"the successor delivery did not drain after the first claim cleared");
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "turn-2", status: "failed" } });
		await secondStarted;
		releaseFirst(true);
		await settle();
		releaseSecond(false);
		await settle();
		const row = dispatcher.statusSnapshot().targets.codex;
		assert.equal(row.orphan.work, secondWork);
		assert.equal(row.orphan.incidentFiled, false,
			"the first orphan's acknowledgement marked its successor filed");
	} finally {
		releaseFirst(false);
		releaseSecond(false);
		await dispatcher.stop();
	}
});

test("a late acknowledgement cannot overwrite the successor's DURABLE marker",
	async () => {
		// The other half of the review's requirement, and the half its own
		// regression cannot see: the in-memory flag belongs to the captured
		// orphan, but the marker on disk belongs to the LIVE fence.
		//
		// Without the identity guard, orphan A's late acknowledgement writes
		// A's record under the live key while the live fence is B. A restart
		// then restores a fence for a claim that was already released and
		// never re-files B's notice — the actionable one.
		const secondWork = W2928;
		const secondEpisode = 2928;
		const secondKey = `work:${secondWork}:${secondEpisode}:g1`;
		const answers = authority([
			OFFERED, HELD, [],
			[entry(secondWork, secondEpisode, false)],
			[entry(secondWork, secondEpisode, true)],
		]);
		let releaseFirst;
		let firstEntered;
		const firstPublication = new Promise((resolve) => { releaseFirst = resolve; });
		const firstStarted = new Promise((resolve) => { firstEntered = resolve; });
		let publications = 0;
		const quarantineDir = freshQuarantineDir();
		const { dispatcher, fake } = bridge({
			revalidate: answers.revalidate,
			quarantineDir,
			runtime: {
				async incident() {
					publications += 1;
					if (publications === 1) {
						firstEntered();
						return firstPublication;
					}
					return false;
				},
			},
		});
		try {
			await ready(dispatcher, fake);
			dispatcher.enqueue(readinessEvent());
			await settle();
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-1", status: "failed" } });
			await firstStarted;
			await new Promise((resolve) => setTimeout(resolve, 5));
			dispatcher.enqueue(readinessEvent({ key: secondKey, work: secondWork,
				episode: secondEpisode }));
			await settle();
			fake.emit("turnCompleted", { threadId: "thread-a",
				turn: { id: "turn-2", status: "failed" } });
			await settle();
			// A's publication finally succeeds, AFTER its fence was cleared
			// and B's took its place.
			releaseFirst(true);
			await settle();
			const marker = JSON.parse(readFileSync(
				join(quarantineDir, `${quarantineKey("local", "thread-a")}.settlement.json`),
				"utf8"));
			assert.equal(marker.work, secondWork,
				"a cleared orphan's late acknowledgement rewrote the live marker");
			assert.equal(marker.incidentFiled, false,
				"the durable marker claims an incident that was refused");
		} finally {
			releaseFirst(false);
			await dispatcher.stop();
		}
	});

test("an accepted turn ABSENT after resume still reconciles its claim",
	async () => {
		// The review says to preserve this ambiguity boundary, and it is
		// preserved: the turn is not replayed. What the boundary is about
		// is whether to re-run the turn, and that stays unanswered. The
		// CLAIM is a different question with a canonical answer — the
		// thread is idle, so nothing is executing the delivery, and if the
		// authority still records the claim the lane is occupied however
		// the turn vanished.
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			const row = await deliverThenReconnect(dispatcher, fake,
				{ status: { type: "idle" }, turns: [] });
			assert.deepEqual({ deliverable: row.deliverable,
				orphan: row.orphan?.work ?? null, incidents: incidents.length },
				{ deliverable: false, orphan: WORK, incidents: 1 },
				"an absent turn cleared without reconciling its surviving claim");
			// Not replayed: the delivery is not re-sent.
			assert.equal(fake.starts.length, 1, "the absent turn was replayed");
			// And the fence names no status, because none was observed.
			assert.equal(row.orphan.status ?? null, null);
		} finally {
			await dispatcher.stop();
		}
	});

test("an absent turn whose claim is GONE leaves the target deliverable",
	async () => {
		// The ordinary reconnect. Nothing is held, so the absent turn is
		// the benign case it has always been and the target drains on.
		const answer = authority([OFFERED, []]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			const row = await deliverThenReconnect(dispatcher, fake,
				{ status: { type: "idle" }, turns: [] });
			assert.equal(row.deliverable, true,
				"an absent turn that orphaned nothing fenced its target");
			assert.equal(incidents.length, 0);
			assert.equal(fake.starts.length, 1);
		} finally {
			await dispatcher.stop();
		}
	});

// FOUND WHILE CORRECTING THE REVIEW'S PATH, not reported in it. The
// resume snapshot is not the only place a terminal managed turn is first
// observed: `#reconcileTarget` also resolves an AMBIGUOUS `turn/start`
// against the snapshot, and `#reconcileAmbiguous` does the same from
// `#drain`. Both bound the delivery and then dropped it on the floor if
// it had already ended, which is the reviewer's defect reached by two
// other routes. Correcting only the reported one would have left them.

test("an ambiguous turn/start resolved on resume as ALREADY FAILED is settled",
	async () => {
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			// A non-protocol failure marks the queued event ambiguous: the
			// dispatcher cannot tell whether the turn started.
			fake.nextTurn = async () => { throw new Error("socket hang up"); };
			const event = readinessEvent();
			const eventId = event.id;
			dispatcher.enqueue(event);
			await settle();
			assert.equal(dispatcher.statusSnapshot().targets.codex.queueDepth, 1,
				"the ambiguous event was not retained");
			// It HAD started, and by resume it has already failed. The
			// resume snapshot carries the user message this dispatcher
			// sent, which is how the ambiguous delivery is recognised.
			fake.nextTurn = null;
			fake.resumeStatus = { type: "idle" };
			fake.resumeTurns = [{ id: "turn-1", status: "failed",
				items: [{ type: "userMessage", clientId: eventId }] }];
			fake.disconnect();
			await new Promise((resolve) => setTimeout(resolve, 30));
			await settle();
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.deepEqual({ deliverable: row.deliverable,
				orphan: row.orphan?.work ?? null, incidents: incidents.length },
				{ deliverable: false, orphan: WORK, incidents: 1 },
				"an ambiguous delivery that had already failed was cleared "
				+ "without reconciling its surviving claim");
		} finally {
			await dispatcher.stop();
		}
	});

test("an ambiguous turn/start resolved by DRAIN as already failed is settled",
	async () => {
		// The third route, and the one resume does not take: the resume
		// snapshot did not carry the delivery, so `#reconcileTarget` left
		// it ambiguous, and `#drain` resolved it against a later
		// `readThread`. Same bound delivery, same terminal turn, same
		// surviving claim — so the same settlement, or the fence depends
		// on which reconciliation happened to see it first.
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			fake.nextTurn = async () => { throw new Error("socket hang up"); };
			const event = readinessEvent();
			dispatcher.enqueue(event);
			await settle();
			assert.equal(dispatcher.statusSnapshot().targets.codex.queueDepth, 1);
			// Resume did NOT resolve it; the later read does.
			fake.nextTurn = null;
			fake.threadTurns = [{ id: "turn-1", status: "failed",
				items: [{ type: "userMessage", clientId: event.id }] }];
			await new Promise((resolve) => setTimeout(resolve, 40));
			await settle();
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.deepEqual({ deliverable: row.deliverable,
				orphan: row.orphan?.work ?? null, incidents: incidents.length },
				{ deliverable: false, orphan: WORK, incidents: 1 },
				"a drain-resolved ambiguous delivery that had already failed "
				+ "was cleared without reconciling its surviving claim");
		} finally {
			await dispatcher.stop();
		}
	});

test("a genuinely interactive turn still reports the runner idle", async () => {
	// The held publication must not swallow the honest one. Nothing is in
	// flight, so a completion for a turn this dispatcher never delivered
	// is exactly what it looks like.
	const answer = authority([OFFERED]);
	const { dispatcher, fake, published } =
		bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "typed-by-a-human", status: "failed" } });
		await settle();
		assert.equal(published.some(([name]) => name === "idle"), true);
		assert.equal(answer.calls.length, 0,
			"a turn with no delivery bound to it was reconciled anyway");
	} finally {
		await dispatcher.stop();
	}
});

// -- correlation --------------------------------------------------------------

test("reconciliation matches the STRUCTURED work and episode", async () => {
	const answer = authority([OFFERED, HELD]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		await deliverThenEnd(dispatcher, fake, "failed");
		assert.deepEqual(answer.calls.at(-1).args,
			["--config", "/home/op/baton.json",
			 "--participant", "baton.codex", "wait", "timeout=0"]);
		assert.equal(dispatcher.statusSnapshot().targets.codex.orphan.correlation,
			"claimed");
	} finally {
		await dispatcher.stop();
	}
});

test("a claim under a DIFFERENT episode still occupies this participant's lane",
	async () => {
		// The exact delivered episode is gone, but a managed participant has
		// one claim slot and its turn has failed. The later episode is therefore
		// the live claim nothing is executing, not evidence that the lane is free.
		const later = [{ kind: "work", action_key: `work:${WORK}:9999:g1`,
			work: WORK, episode_seq: 9999, config_generation: 1, claimed: true }];
		const answer = authority([OFFERED, later]);
		const { dispatcher, fake, published, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			assert.equal(published.some(([name]) => name === "idle"), false);
			assert.equal(incidents.length, 1);
			assert.equal(incidents[0].work, WORK);
			assert.equal(incidents[0].episode, 9999);
			assert.equal(incidents[0].actionKey, `work:${WORK}:9999:g1`);
			assert.equal(dispatcher.statusSnapshot().targets.codex.orphan.correlation,
				"secondary");
		} finally {
			await dispatcher.stop();
		}
	});

test("a delivery with no Work locator reports a HELD lane, not a proven one",
	async () => {
		// A producer at an older build sends neither field. The lane is
		// still provably occupied — a participant holds at most one claim —
		// so the fence is right; the ATTRIBUTION is not proven and the
		// incident says so rather than inventing one.
		const answer = authority([OFFERED, HELD]);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed",
				readinessEvent({ correlated: false }));
			assert.equal(incidents.length, 1);
			assert.equal(incidents[0].work, WORK);
			assert.match(incidents[0].detail, /no Work locator/);
			assert.equal(dispatcher.statusSnapshot().targets.codex.orphan.correlation,
				"held");
		} finally {
			await dispatcher.stop();
		}
	});

// -- the fence ends on canonical evidence, and on nothing else ---------------

test("the fence lifts only when the authority says the claim is gone",
	async () => {
		// The operator's recovery, as the dispatcher sees it: the orphaned
		// claim disappears from the participant's actionable set and the
		// later Work it was blocking is offered unclaimed.
		const stillHeld = [entry(WORK, EPISODE, true), entry(W2928, 9, false)];
		const released = [entry(W2928, 9, false)];
		const answer = authority([OFFERED, stillHeld, stillHeld, released]);
		const { dispatcher, fake, published } =
			bridge({ revalidate: answer.revalidate });
		try {
			await ready(dispatcher, fake);
			await deliverThenEnd(dispatcher, fake, "failed");
			const state = dispatcher.targetStates.get("codex");
			// Still held: the retained event stays retained. The recheck
			// throttle is stepped over rather than slept through, because
			// what is under test is the EVIDENCE the fence ends on, not the
			// interval between two asks.
			state.orphan.checkedAt = 0;
			dispatcher.enqueue(readinessEvent({ key: `work:${W2928}:9:g1`,
				work: W2928, episode: 9 }));
			await settle();
			assert.equal(fake.starts.length, 1,
				"a retained wake was delivered while the lane was still blocked");
			assert.equal(dispatcher.statusSnapshot().targets.codex.deliverable,
				false);
			// Released: the fence lifts and the retained event drains.
			state.orphan.checkedAt = 0;
			void dispatcher.enqueue(readinessEvent({ key: `work:${W2929}:3:g1`,
				work: W2929, episode: 3 }));
			await settle(12);
			assert.equal(dispatcher.statusSnapshot().targets.codex.deliverable,
				true);
			assert.equal(published.at(-1)[0], "idle");
			assert.equal(fake.starts.length, 2,
				"the retained readiness never drained after recovery");
			assert.match(fake.starts[1].text, /W2928/);
		} finally {
			await dispatcher.stop();
		}
	});

// -- durability ---------------------------------------------------------------

function markerPath(dir) {
	const name = readdirSync(dir).find((entry) => entry.endsWith(".settlement.json"));
	return name ? join(dir, name) : null;
}

test("the fence is durable and a dispatcher restart comes back fenced",
	async () => {
		const dir = freshQuarantineDir();
		const first = bridge({ revalidate: authority([OFFERED, SECONDARY_HELD]).revalidate,
			quarantineDir: dir });
		try {
			await ready(first.dispatcher, first.fake);
			await deliverThenEnd(first.dispatcher, first.fake, "failed");
			assert.ok(markerPath(dir), "the fence was never persisted");
			assert.equal(
				first.dispatcher.statusSnapshot().targets.codex.orphan.durable,
				true);
		} finally {
			await first.dispatcher.stop();
		}
		// A NEW process against the SAME rendered thread. Restarting a
		// dispatcher does not release a canonical claim.
		const second = bridge({ revalidate: authority([SECONDARY_HELD]).revalidate,
			quarantineDir: dir });
		try {
			await ready(second.dispatcher, second.fake);
			const row = second.dispatcher.statusSnapshot().targets.codex;
			assert.equal(row.deliverable, false);
			assert.equal(row.restored ?? row.orphan.restored, true);
			assert.equal(row.orphan.work, W2928);
			assert.equal(row.orphan.episode, SECONDARY_EPISODE);
			assert.equal(row.orphan.actionKey, SECONDARY_KEY);
			assert.equal(row.orphan.correlation, "secondary");
			assert.equal(second.published.some(([name]) => name === "failed"),
				true);
			// Already acknowledged, so the restart does NOT re-file it.
			assert.equal(second.incidents.length, 0);
		} finally {
			await second.dispatcher.stop();
		}
	});

test("a fence whose incident was never acknowledged is re-filed once",
	async () => {
		const dir = freshQuarantineDir();
		const key = quarantineKey("local", "thread-a");
		writeFileSync(join(dir, `${key}.settlement.json`), `${JSON.stringify({
			since: 1755000000000, turnId: "turn-1", status: "failed",
			participant: "baton.codex", work: WORK, episode: EPISODE,
			actionKey: KEY, correlation: "claimed", session: "thread-a",
			incidentFiled: false, remedy: "release the exact claim",
		})}\n`);
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: authority([HELD]).revalidate, quarantineDir: dir });
		try {
			await ready(dispatcher, fake);
			assert.equal(incidents.length, 1,
				"a notice the dying process may never have published was lost");
			assert.equal(incidents[0].work, WORK);
			// And the acknowledgement is now durable, so it files ONCE.
			const record = JSON.parse(readFileSync(
				join(dir, `${key}.settlement.json`), "utf8"));
			assert.equal(record.incidentFiled, true);
		} finally {
			await dispatcher.stop();
		}
	});

test("a damaged marker fails closed rather than reading as a clean lane",
	async () => {
		const dir = freshQuarantineDir();
		const key = quarantineKey("local", "thread-a");
		writeFileSync(join(dir, `${key}.settlement.json`), "{ this is not json");
		const { dispatcher, fake, incidents } =
			bridge({ revalidate: authority([HELD]).revalidate, quarantineDir: dir });
		try {
			await ready(dispatcher, fake);
			const row = dispatcher.statusSnapshot().targets.codex;
			assert.equal(row.deliverable, false);
			assert.equal(row.orphan.correlation, "unknown");
			assert.equal(incidents.length, 1,
				"a lost payload vouched for a publication nobody made");
		} finally {
			await dispatcher.stop();
		}
	});

test("a duplicate completion does not count the same failure twice", async () => {
	// A reconnect that replays a terminal event, or an app-server that
	// emits it twice, settles the same turn again — and must not re-mint
	// the fence. Re-minting would reset the durable acknowledgement and
	// file the one failure once per repeat, which is exactly what the
	// acknowledgement exists to prevent.
	const answer = authority([OFFERED, SECONDARY_HELD]);
	const { dispatcher, fake, incidents } =
		bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		const turn = await deliverThenEnd(dispatcher, fake, "failed");
		const reads = answer.calls.length;
		fake.emit("turnCompleted", { threadId: "thread-a", turn });
		await settle();
		assert.ok(answer.calls.length > reads,
			"the repeat was not settled at all, so nothing was under test");
		assert.equal(incidents.length, 1,
			"one failure was filed as two incidents");
		const row = dispatcher.statusSnapshot().targets.codex.orphan;
		assert.equal(row.incidentFiled, true);
		assert.equal(row.turnId, turn.id);
	} finally {
		await dispatcher.stop();
	}
});

// -- claimed-first delivery ---------------------------------------------------

test("the producer forwards claimed Work first, order preserved either side",
	() => {
		const actions = [
			{ kind: "work", action_key: "work:A:1:g1", claimed: false },
			{ kind: "obligation", action_key: "obligation:7" },
			{ kind: "work", action_key: "work:B:2:g1", claimed: true },
			{ kind: "work", action_key: "work:C:3:g1", claimed: false },
		];
		assert.deepEqual(claimedFirst(actions).map((a) => a.action_key),
			["work:B:2:g1", "work:A:1:g1", "obligation:7", "work:C:3:g1"]);
		// Nothing claimed: the authority's own order is returned untouched.
		const none = actions.filter((a) => a.claimed !== true);
		assert.equal(claimedFirst(none), none);
	});

test("a claimed action admitted late is delivered ahead of queued unclaimed work",
	async () => {
		// The dispatcher's own half of the same rule. The producer's fix
		// cannot help an unclaimed event that was already forwarded before
		// the claim was reconciled.
		const answer = authority([[entry(W2928, 9, false),
			entry(WORK, EPISODE, true)]]);
		const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
		try {
			await dispatcher.start({ listen: false });
			// Deliberately NOT idle, so both events queue rather than drain.
			dispatcher.enqueue(readinessEvent({ key: `work:${W2928}:9:g1`,
				work: W2928, episode: 9 }));
			dispatcher.enqueue(readinessEvent({ claimed: true }));
			const queue = dispatcher.targetStates.get("codex").queue;
			assert.deepEqual(queue.map((held) => held.event.action.key),
				[KEY, `work:${W2928}:9:g1`]);
			fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
			await settle();
			assert.match(fake.starts[0].text, /W2907/);
		} finally {
			await dispatcher.stop();
		}
	});

test("promotion never displaces a delivery already in flight", async () => {
	// `#drain` holds the head across an await and `#reconcileTarget` looks
	// it up by position; splicing in front of it would settle the wrong
	// event.
	// W11910 review [P1]: W2928 is revalidated FIRST, while nothing is
	// claimed — which is the realistic ordering for this scenario and the
	// only one the claim-slot rule now permits to start. The promotion
	// arrives after, exactly as the case is about.
	const answer = authority([[entry(W2928, 9, false)],
		[entry(W2928, 9, false), entry(WORK, EPISODE, true)]]);
	const { dispatcher, fake } = bridge({ revalidate: answer.revalidate });
	try {
		await ready(dispatcher, fake);
		let release;
		fake.nextTurn = async (index) => await new Promise((resolve) => {
			release = () => resolve({ id: `turn-${index}`, status: "inProgress" });
		});
		dispatcher.enqueue(readinessEvent({ key: `work:${W2928}:9:g1`,
			work: W2928, episode: 9 }));
		await settle();
		const state = dispatcher.targetStates.get("codex");
		assert.equal(state.draining, true);
		dispatcher.enqueue(readinessEvent({ claimed: true }));
		assert.equal(state.queue[0].event.action.key, `work:${W2928}:9:g1`,
			"the in-flight head was displaced by a late promotion");
		assert.equal(state.queue[1].event.action.key, KEY);
		release();
		await settle();
		assert.equal(state.queue.length, 1,
			"settling the delivery removed the wrong queue entry");
		assert.equal(state.queue[0].event.action.key, KEY);
	} finally {
		await dispatcher.stop();
	}
});
