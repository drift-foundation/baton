// W11910 review [P1]: ONE UNCLAIMED WORK BECOMES A TURN AT A TIME, and
// an undelivered claimed-Work recovery wake is not acknowledged by the
// claim it was going to recover.
//
// `work/records/2026/08/finding-readiness-offer-cleared-before-claim/`.
//
// The two gaps this file closes both survived the first correction
// because each side was checked alone:
//
//   The PRODUCER marks a Work presented the instant the socket accepts
//   it — which in the ACP bridge happens after the prompt returns, and
//   here happens before the turn has even started. Its rotation then
//   admits the next unclaimed Work on the very next unchanged poll. The
//   producer suite asserted exactly that rotation and called it correct;
//   the dispatcher suite never saw the second Work at all. Between them,
//   Work B could queue behind Work A and spend a model turn against a
//   claim slot A had already taken.
//
//   And a first-seen-CLAIMED Work created a `pending` offer, emitted one
//   recovery wake, and — if that delivery failed — had its `pending`
//   entry acknowledged by the very `claimed:true` it was trying to
//   recover. `pending` was carrying two meanings: "an offer nobody has
//   answered" and "a wake nobody received". A claim can answer the
//   first; nothing about it answers the second.
//
// So this file crosses the boundary deliberately: the producer's own
// emissions are fed to a real `EventBridge`, and what is asserted is
// which deliveries become TURNS.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { ReadinessOffers, actionEvent } from "../src/codex_baton_bridge.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";
import { FIXTURE_POLICY } from "./stale_episode.test.mjs";

const quiet = { info() {}, warn() {}, error() {}, debug() {} };
const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";
const A = "7ba67cb8-W6630";
const B = "7ba67cb8-W6632";

class FakeClient extends EventEmitter {
	constructor() {
		super();
		this.connected = true;
		this.starts = [];
		this.nextTurn = null;
	}

	async connectAndInitialize() {
		this.connected = true;
		this.emit("connected", {});
	}

	async startTurn(threadId, text, clientId) {
		this.starts.push({ threadId, text, clientId });
		return this.nextTurn
			? await this.nextTurn(this.starts.length)
			: { id: `turn-${this.starts.length}`, status: "inProgress" };
	}

	async resume(threadId) {
		return { thread: { id: threadId, status: { type: "idle" }, turns: [] } };
	}

	async readThread(threadId) {
		return { id: threadId, status: { type: "idle" }, turns: [] };
	}

	disconnect() {
		const was = this.connected;
		this.connected = false;
		if (was) this.emit("disconnected");
	}
}

function action(work, { claimed = false, episode = 1 } = {}) {
	return { kind: "work", action_key: `work:${work}:${episode}:g1`,
		work, local_id: work.split("-").pop(), title: `do ${work}`,
		phase: claimed ? "active" : "queued", claimed,
		episode_seq: episode, config_generation: 1 };
}

function obligation(seq = 7) {
	return { kind: "obligation", action_key: `obligation:${seq}`, seq,
		work: A, flavor: "response" };
}

/** A CANONICAL envelope, not an abbreviation of one. The dispatcher's
 *  revalidation applies the same typed v11 contract the producers do, so a
 *  fixture that omitted the protocol fields would be scheduling from a reply
 *  the real authority never emits. */
function envelope(actionable) {
	return { protocol_version: 11, projection_version: "12.4",
		authority_uuid: UUID, participant: "baton.codex", snapshot_seq: 1,
		result: { timed_out: false, actionable } };
}

async function settle(times = 10) {
	for (let index = 0; index < times; index += 1) {
		await new Promise((resolve) => setImmediate(resolve));
	}
}

/** The dispatcher, plus a scripted canonical projection it revalidates
 *  every delivery against. `level()` is what `wait timeout=0` answers
 *  right now, so a test moves the world by moving that one value. */
function dispatcher({ revalidate, logger } = {}) {
	const fake = new FakeClient();
	let level = [];
	const bridge = new EventBridge({
		config: validateConfig({
			servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
			targets: { codex: { server: "local", threadId: "thread-a",
				identity: { participant: "baton.codex", role: "rview",
					actionOwner: "baton.slaw" } } },
			roleInstructions: { binary: "/opt/baton/bin/baton",
				config: "/home/op/baton.json", execPolicyFile: FIXTURE_POLICY },
			eventSocket: "/tmp/codex-w11910-unused.sock",
			quarantineDir: freshQuarantineDir(),
			claimSlotRetryMs: 5,
			reconnectMinMs: 1, reconnectMaxMs: 2 }),
		logger: logger ?? quiet,
		clientFactory: () => fake,
		runtimeFactory: () => ({ incarnation: "run-1", async start() {},
			async state() {}, async incident() { return true; },
			async facts() { return true; }, async end() {} }),
		revalidate: revalidate ?? (async () => ({ stdout: JSON.stringify(
			envelope(level)) })),
	});
	return { bridge, fake, set: (next) => { level = next; } };
}

async function ready(bridge, fake) {
	await bridge.start({ listen: false });
	fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
	await settle();
}

function started(fake) {
	return fake.starts.map((entry) => entry.clientId);
}

test("B never becomes a turn while A's delivery is in flight, however "
	+ "often the unchanged level is polled", async () => {
	const { bridge, fake, set } = dispatcher();
	const offers = new ReadinessOffers({ now: () => 0, retryMs: 1 });
	try {
		await ready(bridge, fake);
		// A's turn opens and does not return: this is the window the
		// producer cannot see, and the whole finding.
		let release;
		fake.nextTurn = async (index) => await new Promise((resolve) => {
			release = () => resolve({ id: `turn-${index}`, status: "inProgress" });
		});
		const level = [action(A), action(B)];
		set(level);
		// THE PRODUCER'S OWN ROTATION, unchanged: poll the same level
		// repeatedly and it emits A, then B. That is correct of the
		// producer and is not, by itself, a second turn.
		const emitted = [];
		for (let poll = 0; poll < 4; poll += 1) {
			for (const one of offers.sync(envelope(level))) {
				const event = actionEvent(envelope(level), one,
					{ target: "codex" });
				emitted.push(bridge.enqueue(event));
				offers.markPresented(envelope(level), one);
			}
			await settle();
		}
		assert.ok(emitted.length >= 2,
			"the producer did not rotate; this case has nothing to prove");
		// AND EXACTLY ONE TURN. B may be retained — retention is what
		// keeps the offer alive — but it must not run.
		assert.deepEqual(started(fake),
			[`baton-v11:${UUID}:baton.codex:work:${A}:1:g1`],
			"a second Work started while the first delivery was in flight");
		// A CLAIMS, and its turn ends. The slot is now occupied by A,
		// so B still cannot start.
		set([action(A, { claimed: true }), action(B)]);
		release();
		await settle();
		fake.emit("turnCompleted", { threadId: "thread-a",
			turn: { id: "turn-1", status: "completed" } });
		await settle(20);
		assert.equal(started(fake).length, 1,
			"B spent a turn against a claim slot A was holding");
		// The claim passes or closes. The SAME retained delivery is
		// spent now, with no restart and no new event.
		set([action(B)]);
		await new Promise((resolve) => setTimeout(resolve, 40));
		await settle(20);
		assert.deepEqual(started(fake).map((id) => id.endsWith(`${B}:1:g1`)),
			[false, true],
			"the retained offer never ran after the claim slot freed");
	} finally {
		await bridge.stop();
	}
});

test("a deferred delivery is held, never dropped, and needs no new event",
	async () => {
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const dropped = [];
		bridge.on("actionDropped", (entry) => dropped.push(entry));
		set([action(A, { claimed: true }), action(B)]);
		bridge.enqueue(actionEvent(envelope([action(B)]), action(B),
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0, "it started against a held claim");
		assert.deepEqual(dropped, [],
			"a deferred offer was DROPPED; the level would then need a "
			+ "new episode to come back, which is this Work's own defect");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1, "the offer was not retained");
	} finally {
		await bridge.stop();
	}
});

test("a claimed Work's own recovery delivery is never deferred", async () => {
	// It IS the claim. Holding it behind itself would strand exactly the
	// participant this recovery path exists to reach.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		set([action(A, { claimed: true })]);
		bridge.enqueue(actionEvent(envelope([action(A, { claimed: true })]),
			action(A, { claimed: true }), { target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 1,
			"the participant's own claimed Work was held behind its own claim");
	} finally {
		await bridge.stop();
	}
});

test("an unclaimed delivery promoted to claimed while queued becomes its "
	+ "own recovery turn", async () => {
	// The action key survives the claim.  Scheduling from the stale
	// `claimed:false` bit in the queued event would hold this delivery
	// behind the very claim it now exists to recover.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(A);
		set([action(A, { claimed: true })]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 1,
			"a queued offer was held behind its own newly recorded claim");
	} finally {
		await bridge.stop();
	}
});

test("a non-Work obligation is not held behind the participant's claim",
	async () => {
	// The one-claim slot constrains Work offers.  Obligations, trials and
	// pokes retain their existing delivery rule under the confirmed
	// boundary, even when the participant is already handling Work.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const owed = obligation();
		set([action(A, { claimed: true }), owed]);
		bridge.enqueue(actionEvent(envelope([owed]), owed,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 1,
			"the Work claim-slot gate swallowed a non-Work obligation");
	} finally {
		await bridge.stop();
	}
});

test("a deferred Work at the queue head does not hold a later obligation",
	async () => {
	// The claim-slot rule applies only to Work.  The earlier case starts with
	// the obligation at the head; this one exercises the retained-queue state
	// that motivated W11910. B is already queued and deferred behind claimed
	// A when an obligation arrives. Keeping B at the FIFO head makes the
	// Work-only gate swallow the obligation indirectly and can deadlock a
	// participant whose live Work needs that directed answer before it ends.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const owed = obligation();
		set([action(A, { claimed: true }), offered]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"the deferred Work unexpectedly spent a turn");
		set([action(A, { claimed: true }), offered, owed]);
		bridge.enqueue(actionEvent(envelope([owed]), owed,
			{ target: "codex" }));
		await settle(20);
		assert.deepEqual(started(fake),
			[`baton-v11:${UUID}:baton.codex:obligation:${owed.seq}`],
			"a Work-only claim-slot gate held the later obligation");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the Work offer was not retained after the obligation passed it");
	} finally {
		await bridge.stop();
	}
});

test("an ambiguous obligation behind a deferred Work is reconciled",
	async () => {
	// Passing the Work-only barrier makes this obligation the delivery being
	// attempted even though B remains at queue[0]. If turn/start loses its
	// response after the turn was created, reconciliation must follow THAT
	// candidate rather than looking only at the retained Work head. Otherwise
	// the ambiguous obligation is skipped on every retry and its live turn is
	// never bound to this dispatcher.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const owed = obligation();
		set([action(A, { claimed: true }), offered]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		const event = actionEvent(envelope([owed]), owed,
			{ target: "codex" });
		fake.nextTurn = async () => {
			throw new Error("connection dropped after send");
		};
		fake.resume = async (threadId) => ({ thread: { id: threadId,
			status: { type: "active" }, turns: [{ id: "turn-owed",
				status: "inProgress", items: [{ type: "userMessage",
					clientId: event.id }] }] } });
		set([action(A, { claimed: true }), offered, owed]);
		bridge.enqueue(event);
		await settle(30);
		assert.equal(started(fake).length, 1,
			"the obligation was retried after its delivered turn was found");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the delivered ambiguous obligation stayed stranded behind B");
	} finally {
		await bridge.stop();
	}
});

test("a disconnected ambiguous obligation behind a deferred Work is "
	+ "reconciled by the next drain", async () => {
	// This is the half the seventh correction left unmeasured. A transport
	// drop after `turn/start` skips the catch branch's immediate reconciliation.
	// On reconnect, the resume snapshot can still miss the just-created turn;
	// the following ordinary drain must therefore select the ambiguous
	// obligation behind B and reconcile it by client message id. Looking only
	// at queue[0] leaves it skipped forever by the claim-slot scan.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const owed = obligation();
		set([action(A, { claimed: true }), offered]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		const event = actionEvent(envelope([owed]), owed,
			{ target: "codex" });
		fake.nextTurn = async () => {
			fake.disconnect();
			throw new Error("connection dropped after send");
		};
		// The reconnect snapshot does not yet carry the turn. The next direct
		// read does, which isolates the ordinary-drain reconciliation branch.
		fake.resume = async (threadId) => ({ thread: { id: threadId,
			status: { type: "idle" }, turns: [] } });
		fake.readThread = async (threadId) => ({ id: threadId,
			status: { type: "active" }, turns: [{ id: "turn-owed",
				status: "inProgress", items: [{ type: "userMessage",
					clientId: event.id }] }] });
		set([action(A, { claimed: true }), offered, owed]);
		bridge.enqueue(event);
		await new Promise((resolve) => setTimeout(resolve, 40));
		await settle(30);
		assert.equal(started(fake).length, 1,
			"the disconnected ambiguous obligation was replayed");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the disconnected ambiguous obligation stayed behind B");
	} finally {
		await bridge.stop();
	}
});

// The review's requirement has a second half: what may pass the barrier is
// exactly one thing, and TWO things must not. Both fall out of the verdict
// rather than being enumerated in the scan -- which is worth proving, because
// a rule that holds by consequence is a rule nothing would notice losing.

test("a second unclaimed Work does not rotate past a deferred one",
	async () => {
	// C is behind B, both unclaimed, both waiting on A's claim. If the scan
	// admitted anything that was not the head it would start C against the
	// same occupied slot -- which is the model turn spent on a refusal that
	// this whole Work exists to stop. Nothing special refuses it: C is asked
	// the same question B was and gets the same `deferred` answer.
	const { bridge, fake, set } = dispatcher();
	const C = "7ba67cb8-W6633";
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const second = action(C);
		set([action(A, { claimed: true }), offered, second]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		bridge.enqueue(actionEvent(envelope([second]), second,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"an unclaimed Work rotated past another one into the claim slot");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 2,
			"a retained offer was dropped rather than held");
	} finally {
		await bridge.stop();
	}
});

test("a generic non-readiness event does not rotate past a deferred Work",
	async () => {
	// An event with no v11 action block is not readiness at all, and
	// `#revalidate` answers `live` for one by construction -- it has nothing
	// to ask the authority about. So this is the candidate the scan has to
	// refuse BEFORE the read rather than because of it, and it is the one the
	// review named. Ordinary FIFO order is the whole of its rule: it takes
	// its turn when it reaches the head.
	const warned = [];
	const { bridge, fake, set } = dispatcher({
		logger: { ...quiet, warn: (line) => warned.push(line) } });
	try {
		await ready(bridge, fake);
		const offered = action(B);
		set([action(A, { claimed: true }), offered]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		const admitted = bridge.enqueue({ id: "generic-1", target: "codex",
			source: "operator", type: "note", summary: "not readiness",
			details: "" });
		assert.equal(admitted.accepted, true,
			"this case never queued the event it is about");
		await settle(20);
		assert.equal(started(fake).length, 0,
			"a non-readiness event was rotated past a deferred Work");
		// AND NO FAULT, which is the assertion that actually discriminates.
		// Measured: with the pre-read guard removed the scan reaches an event
		// with no action block, and what that produces is not a rotation --
		// the barrier faults, the head is marked ambiguous, and every retry
		// repeats it. Turn ORDER survives that, so a case asserting only
		// order would pass either way and prove nothing about the guard.
		assert.deepEqual(warned, [],
			"the claim-slot scan faulted on an event carrying no action");
		// AND THE ORDER, which is the review's own requirement:
		// removing the guard makes the scan reach an event with no action
		// block at all, and what that produces is a fault rather than a
		// rotation -- so a case asserting only that nothing started would
		// pass either way and prove nothing. Measured: with the guard
		// removed this assertion is what goes red.
		set([offered]);
		// A REAL delay, not a microtask drain: the barrier's own retry is the
		// only thing that re-examines the head once the claim disappears, and
		// it is scheduled on the bounded cadence rather than immediately.
		await new Promise((resolve) => setTimeout(resolve, 80));
		await settle(30);
		// B FIRST. The generic event does not follow in this window and is
		// not expected to: one turn runs at a time, and B's is still open.
		// What is asserted is that nothing got AHEAD of it.
		assert.equal(started(fake)[0],
			`baton-v11:${UUID}:baton.codex:${offered.action_key}`,
			"a non-readiness event took the turn the deferred Work was owed");
	} finally {
		await bridge.stop();
	}
});

test("a claimed Work behind a deferred one is its own recovery and passes",
	async () => {
	// The promotion the review said to preserve, proved rather than assumed.
	// A claimed Work is the participant's OWN live assignment being
	// recovered, which `#revalidate` already calls `live` and which the
	// module docstring calls the one delivery that must never wait -- so it
	// passes the barrier for the same reason an obligation does, and needs no
	// rule of its own to do it.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const held = action(A, { claimed: true });
		set([held, offered]);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		bridge.enqueue(actionEvent(envelope([held]), held,
			{ target: "codex" }));
		await settle(20);
		assert.deepEqual(started(fake),
			[`baton-v11:${UUID}:baton.codex:${held.action_key}`],
			"a claimed Work's own recovery was held behind an offer");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the deferred offer was not retained after the recovery passed");
	} finally {
		await bridge.stop();
	}
});

test("the deferred Work keeps the head and its in-flight identity throughout "
	+ "a passing action's ambiguity", async () => {
	// The other half of the seventh review's requirement, and the half nothing
	// asserted: reconciling the passing candidate must not disturb B. If B
	// lost its in-flight identity here, the producer's next level-triggered
	// re-send would be accepted as a NEW delivery and B would be queued behind
	// itself -- which is the duplicate the in-flight retention exists to stop,
	// reached by a path the sixth correction opened.
	const { bridge, fake, set } = dispatcher();
	try {
		await ready(bridge, fake);
		const offered = action(B);
		const owed = obligation();
		set([action(A, { claimed: true }), offered]);
		const first = bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		assert.equal(first.accepted, true);
		await settle(20);
		const event = actionEvent(envelope([owed]), owed, { target: "codex" });
		fake.nextTurn = async () => {
			throw new Error("connection dropped after send");
		};
		fake.resume = async (threadId) => ({ thread: { id: threadId,
			status: { type: "active" }, turns: [{ id: "turn-owed",
				status: "inProgress", items: [{ type: "userMessage",
					clientId: event.id }] }] } });
		set([action(A, { claimed: true }), offered, owed]);
		bridge.enqueue(event);
		await settle(30);
		// B is still the only thing queued, and still IN FLIGHT: the producer
		// re-sending the same unchanged offer is refused rather than queued
		// behind itself.
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"B did not keep the head after the passing action reconciled");
		const again = bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		assert.equal(again.accepted, false, "B's in-flight identity was lost");
		assert.equal(again.reason, "in-flight");
	} finally {
		await bridge.stop();
	}
});

test("an unreadable claim-slot projection is retained without spending a turn",
	async () => {
	// Unknown is not live. If the immediate canonical read cannot say
	// whether this participant already holds Work, starting the queued offer
	// spends a model turn against a slot the dispatcher has not proved free.
	const { bridge, fake } = dispatcher({
		revalidate: async () => { throw new Error("baton unavailable"); },
	});
	try {
		await ready(bridge, fake);
		const offered = action(B);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"an unreadable claim-slot projection was treated as live");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the uncertain offer was dropped instead of retained");
	} finally {
		await bridge.stop();
	}
});

test("a malformed matching action cannot masquerade as non-Work and bypass "
	+ "the claim slot", async () => {
	// The immediate read now schedules from the matching entry's `kind` and
	// `claimed` fields.  A present actionable array is not enough: those
	// fields need the same typed-contract validation as the producer read.
	// This entry carries B's Work key but claims the known obligation kind,
	// whose structured locator contradicts that key.  Treating it as an
	// ordinary non-Work action would spend B's turn while A owns the slot.
	const offered = action(B);
	const malformed = { kind: "obligation", action_key: offered.action_key,
		seq: 7, work: B };
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify({
			protocol_version: 11, projection_version: "12.4",
			authority_uuid: UUID, participant: "baton.codex", snapshot_seq: 1,
			result: { timed_out: false,
				actionable: [action(A, { claimed: true }), malformed] },
		}) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"a malformed matching action bypassed the occupied claim slot");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the uncertain offer was not retained for a valid authority read");
	} finally {
		await bridge.stop();
	}
});

test("a malformed NEIGHBOUR makes the read unreadable, not just a malformed "
	+ "match", async () => {
	// ONE FIELD OVER from the review's case, and the same defect.
	//
	// The review's entry was the MATCHING one, so typing only the match would
	// have answered it. But the occupied-slot question is answered from the
	// entries that are NOT the match — `some(kind === "work" && claimed)` —
	// so an unreadable neighbour disqualifies the read exactly as much. Here
	// the matching B offer is perfectly formed and A, the entry that would
	// report the slot occupied, carries a `claimed` this contract rejects.
	// A gate that trusted `=== true` would read A as unclaimed and start B.
	const offered = action(B);
	const badNeighbour = { ...action(A), claimed: "true" };
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify(
			envelope([badNeighbour, offered])) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"an unreadable neighbour still answered the claim-slot question");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the uncertain offer was not retained");
	} finally {
		await bridge.stop();
	}
});

test("a Work neighbour with no claimed verdict cannot answer that the slot is "
	+ "free", async () => {
	// `claimed` is no longer merely trusted prose: this gate uses it to decide
	// whether another Work owns the participant's one claim slot.  The shared
	// validator rejects a wrong type but still accepts the field's absence, so
	// a structurally incomplete neighbour currently falls through
	// `claimed === true` and authorizes B's turn.  An unread claim bit cannot
	// prove a free slot; it is the same uncertain envelope as the wrong-typed
	// neighbour above.
	const offered = action(B);
	const badNeighbour = action(A, { claimed: true });
	delete badNeighbour.claimed;
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify(
			envelope([badNeighbour, offered])) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"a missing claim verdict was interpreted as an unclaimed Work");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the incomplete projection was not retained as uncertain");
	} finally {
		await bridge.stop();
	}
});

test("an envelope answering about another participant is not authority for "
	+ "this episode", async () => {
	// The read names `--participant baton.codex`. An answer that describes
	// somebody else's actionable set proves neither that this episode still
	// exists nor that this participant's claim slot is free, however
	// well-formed each entry in it is — and this deployment has already been
	// bitten once by a readiness action reaching the wrong participant.
	const offered = action(B);
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify(
			{ ...envelope([offered]), participant: "baton.tuner" }) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"another participant's projection authorized this turn");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"the uncertain offer was not retained");
	} finally {
		await bridge.stop();
	}
});

test("a key carried under a kind this build does not know is retained, not "
	+ "read as withdrawn", async () => {
	// The contract is deliberately liberal about unknown kinds: it drops them
	// from the actionable set and records them under `ignored_actions` so a
	// newer authority can add a primitive without breaking an older bridge.
	// That tolerance is about DELIVERY and says nothing about whether the
	// episode is over — the authority is still naming this exact key. Reading
	// the removal as withdrawal would be this Work's own defect one layer
	// down: a level cleared by something that is not a claim.
	const offered = action(B);
	const unknown = { kind: "escalation", action_key: offered.action_key,
		work: B };
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify(
			envelope([unknown])) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"an unknown kind was delivered as if this build understood it");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 1,
			"an ignored entry carrying the exact key was read as withdrawal");
	} finally {
		await bridge.stop();
	}
});

test("a key the authority no longer names at all is still dropped", async () => {
	// The other half of the case above, and the one that keeps the retention
	// honest: absence from a READABLE answer is authoritative withdrawal, and
	// this correction must not turn every absence into an offer held forever.
	const offered = action(B);
	const { bridge, fake } = dispatcher({
		revalidate: async () => ({ stdout: JSON.stringify(
			envelope([action(A)])) }),
	});
	try {
		await ready(bridge, fake);
		bridge.enqueue(actionEvent(envelope([offered]), offered,
			{ target: "codex" }));
		await settle(20);
		assert.equal(started(fake).length, 0,
			"a withdrawn episode became a turn");
		assert.equal(bridge.handleRequest({ control: "status" })
			.targets.codex.queueDepth, 0,
			"a withdrawn episode was retained instead of dropped");
	} finally {
		await bridge.stop();
	}
});

// -- the failed claimed-Work recovery wake ------------------------------------

test("a claimed-Work recovery wake whose delivery failed is offered again",
	async () => {
	const offers = new ReadinessOffers({ now: () => 0, retryMs: 1 });
	const held = action(A, { claimed: true });
	const level = envelope([held]);
	// First poll: first seen already claimed, so one recovery wake.
	assert.deepEqual(offers.sync(level).map((one) => one.action_key),
		[held.action_key]);
	// The transport failed, so `markPresented` is deliberately not
	// called — exactly what both adapters do on a delivery failure.
	assert.deepEqual(offers.sync(level).map((one) => one.action_key),
		[held.action_key],
		"the claim acknowledged a wake that never reached the runner");
	assert.equal(offers.retained(level, held), true,
		"the undelivered recovery wake was forgotten");
	// And once it lands, the claim it recovers is its own answer.
	offers.markPresented(level, held);
	assert.deepEqual(offers.sync(level), []);
	assert.equal(offers.retained(level, held), false);
});

test("a delivered recovery wake is not repeated on any later poll", async () => {
	const offers = new ReadinessOffers({ now: () => 0, retryMs: 1 });
	const held = action(A, { claimed: true });
	const level = envelope([held]);
	offers.markPresented(level, offers.sync(level)[0]);
	for (let poll = 0; poll < 5; poll += 1) {
		assert.deepEqual(offers.sync(level), [],
			"the recovery wake was spent more than once");
	}
});

test("an offer this adapter MADE is still acknowledged by the claim",
	async () => {
	// The other half of the same distinction: `recovering` must not
	// swallow the acknowledgement the whole correction turns on.
	const offers = new ReadinessOffers({ now: () => 0, retryMs: 1 });
	const offered = action(A);
	const open = envelope([offered]);
	offers.markPresented(open, offers.sync(open)[0]);
	const taken = envelope([action(A, { claimed: true })]);
	assert.deepEqual(offers.sync(taken), [],
		"the claim did not acknowledge the offer it answered");
	assert.equal(offers.retained(taken, offered), false);
	for (let poll = 0; poll < 5; poll += 1) {
		assert.deepEqual(offers.sync(taken), []);
	}
});
