import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";

class FakeClient extends EventEmitter {
  constructor() {
    super();
    this.connected = true;
    this.starts = [];
    this.start = async (threadId) => ({ id: `turn-${threadId}`, status: "inProgress" });
    this.resumes = [];
    this.responses = [];
    this.interrupts = [];
    this.interruptFails = false;
    this.canRespond = true;
  }

  async connectAndInitialize() {
    this.connected = true;
    this.emit("connected", {});
  }

  // W3243: what this bridge answered a SERVER-initiated request with,
  // and which turns it ended. "It denied and never approved" is the
  // assertion this Work exists for, so the fake records both.
  respondError(id, code, message) {
    this.responses.push({ id, code, message });
    return this.canRespond;
  }

  async interruptTurn(threadId, turnId) {
    this.interrupts.push({ threadId, turnId });
    if (this.interruptFails) throw new Error("interrupt refused");
    return { ok: true };
  }

  async startTurn(threadId, text, clientId) {
    this.starts.push({ threadId, text, clientId });
    return await this.start(threadId, text, clientId);
  }

  async resume(threadId) {
    this.resumes.push(threadId);
    return { thread: { id: threadId, status: { type: "idle" }, turns: [] } };
  }

  async readThread(threadId) {
    return { id: threadId, status: { type: "idle" }, turns: [] };
  }

  disconnect() {
    const wasConnected = this.connected;
    this.connected = false;
    if (wasConnected) this.emit("disconnected");
  }
}

function config(overrides = {}) {
  return validateConfig({
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      a: { server: "local", threadId: "thread-a" },
      b: { server: "local", threadId: "thread-b" },
      c: { server: "local", threadId: "thread-c" },
    },
    eventSocket: "/tmp/codex-event-bridge-test-unused.sock",
    quarantineDir: freshQuarantineDir(),
    ...overrides,
  });
}

function bridgeWithFake(configuration = config()) {
  const fake = new FakeClient();
  const quiet = { info() {}, warn() {}, error() {}, debug() {} };
  const bridge = new EventBridge({ config: configuration, logger: quiet, clientFactory: () => fake });
  return { bridge, fake };
}

function event(target, summary = "failed") {
  return { target, source: "build", type: "build-failed", summary };
}

test("deduplicates per target", () => {
  const { bridge } = bridgeWithFake();
  assert.equal(bridge.enqueue(event("a")).accepted, true);
  assert.equal(bridge.enqueue(event("a")).reason, "duplicate");
  assert.equal(bridge.enqueue(event("b")).accepted, true);
});

test("applies per-target and global queue bounds", () => {
  const { bridge } = bridgeWithFake(config({ maxQueuePerTarget: 2, maxQueueTotal: 2 }));
  assert.equal(bridge.enqueue(event("a", "one")).accepted, true);
  assert.equal(bridge.enqueue(event("a", "two")).accepted, true);
  assert.equal(bridge.enqueue(event("a", "three")).reason, "target-queue-full");
  assert.equal(bridge.enqueue(event("b", "one")).reason, "global-queue-full");
});

test("dispatches independent idle targets concurrently", async () => {
  const { bridge, fake } = bridgeWithFake();
  const resolvers = [];
  fake.start = async (threadId) => await new Promise((resolve) => resolvers.push(() => resolve({ id: `turn-${threadId}`, status: "inProgress" })));
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  fake.emit("status", { threadId: "thread-b", status: { type: "idle" } });
  bridge.enqueue(event("a"));
  bridge.enqueue(event("b"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.deepEqual(fake.starts.map((start) => start.threadId).sort(), ["thread-a", "thread-b"]);
  for (const resolve of resolvers) resolve();
  await new Promise((resolve) => setImmediate(resolve));
});

test("does not dispatch an unrelated idle target", async () => {
  const { bridge, fake } = bridgeWithFake();
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  bridge.enqueue(event("b"));
  await new Promise((resolve) => setImmediate(resolve));
  assert.equal(fake.starts.length, 0);
});

test("reports ready only after every configured target is loaded", () => {
  const { bridge, fake } = bridgeWithFake();
  assert.equal(bridge.handleRequest({ control: "status" }).ready, false);
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  fake.emit("status", { threadId: "thread-b", status: { type: "inProgress" } });
  assert.equal(bridge.handleRequest({ control: "status" }).ready, false);
  fake.emit("status", { threadId: "thread-c", status: { type: "idle" } });
  const status = bridge.handleRequest({ control: "status" });
  assert.equal(status.ready, true);
  // W3243 widened every target row with the delivery diagnostics an
  // operator needs when one wedges. The three facts this test always
  // asserted are unchanged; `deliverable` is the new one that matters,
  // and an in-progress turn nobody is blocked on is still deliverable.
  assert.deepEqual(status.targets.b, {
    connected: true, loaded: true, status: "inProgress",
    deliverable: true, participant: null, threadId: "thread-b",
    queueDepth: 0, oldestQueuedMs: null, blocked: null,
    // W99 added the sticky context condition beside the live one. A
    // target nobody has ever asked for approval on is not quarantined.
    tainted: null,
  });
});

test("reconciles ambiguous delivery by client message id before retry", async () => {
  const { bridge, fake } = bridgeWithFake();
  let deliveredId;
  fake.start = async (_threadId, _text, clientId) => {
    deliveredId = clientId;
    throw new Error("connection dropped after send");
  };
  fake.resume = async (threadId) => ({
    thread: {
      id: threadId,
      status: { type: "idle" },
      turns: [{ id: "delivered-turn", status: "completed", items: [{ type: "userMessage", clientId: deliveredId }] }],
    },
  });
  fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
  bridge.enqueue(event("a"));
  await new Promise((resolve) => setTimeout(resolve, 10));
  assert.equal(fake.starts.length, 1);
  assert.equal(bridge.globalQueueDepth, 0);
});

test("initial connection resumes every configured target", async () => {
  const temporary = await import("node:fs/promises");
  const os = await import("node:os");
  const path = await import("node:path");
  const directory = await temporary.mkdtemp(path.join(os.tmpdir(), "codex-event-bridge-test-"));
  const configuration = config({ eventSocket: path.join(directory, "events.sock") });
  const { bridge, fake } = bridgeWithFake(configuration);
  try {
    await bridge.start({ listen: false });
    const deadline = Date.now() + 1000;
    while (fake.resumes.length < 3 && Date.now() < deadline) await new Promise((resolve) => setTimeout(resolve, 5));
    assert.deepEqual(fake.resumes.sort(), ["thread-a", "thread-b", "thread-c"]);
    assert.equal(bridge.statusSnapshot().ready, true);
  } finally {
    await bridge.stop();
    await temporary.rm(directory, { recursive: true });
  }
});

// -- W3243: a wedged target turn must not swallow readiness ----------------
//
// The incident. `baton.codex`'s target thread entered
// waiting-input(approval) at 04:07:47Z and never left it. The producer
// kept forwarding and the dispatcher kept logging
// "unavailable or active; queued (N)" until 24 events were stacked
// behind that one turn, and the stack still reported the target
// healthy because it was connected and loaded. The reviewer found
// W2938 only by invoking canonical `wait` by hand.
//
// The ruled v11 boundary: dispatcher-owned readiness turns are
// NON-INTERACTIVE. Deny the request, end the turn within a bound,
// retain and drain what queued, and report unhealthy until the turn is
// actually over — without ever approving anything.

function approvalRequest(threadId = "thread-a", id = 7) {
  return { id, method: "item/commandExecution/requestApproval",
           params: { threadId } };
}

function readyEvent(target, id) {
  return { target, source: "baton", type: "v11-action-ready",
           summary: `W${id} is ready`,
           details: `work:W${id}:1:g1` };
}

test("W3243: an approval request is denied rather than left unanswered",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    fake.emit("serverRequest", approvalRequest());
    assert.equal(fake.responses.length, 1,
      "the request was left unanswered, which is what wedged the turn");
    assert.equal(fake.responses[0].id, 7);
    assert.match(fake.responses[0].message, /cannot approve/);
    await bridge.stop();
  });

test("W3243: denying is not approving", async () => {
  // The boundary that must survive this correction: no path here ever
  // sends a decision an app-server could read as permission.
  const { bridge, fake } = bridgeWithFake();
  await bridge.start({ listen: false });
  fake.emit("serverRequest", approvalRequest());
  for (const response of fake.responses) {
    assert.ok(response.code, "a denial is an error response, not a result");
    assert.doesNotMatch(String(response.message), /approve[d]?\b(?! commands)/i);
  }
  await bridge.stop();
});

test("W3243: a blocked target reports undeliverable and unhealthy",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    for (const thread of ["thread-a", "thread-b", "thread-c"]) {
      fake.emit("status", { threadId: thread, status: { type: "idle" } });
    }
    assert.equal(bridge.handleRequest({ control: "status" }).ready, true);
    fake.emit("serverRequest", approvalRequest());
    const status = bridge.handleRequest({ control: "status" });
    assert.equal(status.ready, false,
      "the stack reported healthy while a target could take no delivery");
    assert.equal(status.targets.a.deliverable, false);
    assert.equal(status.targets.a.connected, true,
      "loaded-but-unable must stay distinguishable from disconnected");
    assert.equal(status.targets.a.loaded, true);
    assert.equal(status.targets.b.deliverable, true,
      "one wedged target made another look unhealthy");
    await bridge.stop();
  });

test("W3243: the diagnostics name the thread, turn, cause and queue",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-a", status: { type: "inProgress" } });
    fake.emit("serverRequest", approvalRequest());
    bridge.enqueue(readyEvent("a", 1));
    bridge.enqueue(readyEvent("a", 2));
    const target = bridge.handleRequest({ control: "status" }).targets.a;
    assert.equal(target.threadId, "thread-a");
    assert.equal(target.blocked.cause, "approval");
    assert.match(target.blocked.method, /requestApproval/);
    assert.equal(target.blocked.denied, true);
    assert.ok(target.blocked.ageMs >= 0);
    assert.equal(target.queueDepth, 2,
      "the queue depth an operator needs is not reported");
    assert.ok(target.oldestQueuedMs !== null,
      "how long delivery has been stuck is not reported");
    await bridge.stop();
  });

test("W3243: more than one readiness event is RETAINED, not lost",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-a", status: { type: "inProgress" } });
    fake.emit("serverRequest", approvalRequest());
    for (let index = 1; index <= 3; index += 1) {
      const result = bridge.enqueue(readyEvent("a", index));
      assert.equal(result.accepted, true,
        "a readiness event was dropped because its target wedged");
    }
    assert.equal(bridge.handleRequest({ control: "status" }).targets.a.queueDepth, 3);
    await bridge.stop();
  });

test("W3243+W99: the turn ending clears the live block and NOTHING else",
  async () => {
    // SUPERSEDED HALF, deliberately rewritten. This test used to assert
    // that the target became deliverable again and redelivered the
    // retained events once its turn ended. The approver's 2026-08-21
    // ruling (see `finding-managed-turn-approval-incidents/FINDING.md`
    // and the scoped supersession in
    // `finding-readiness-target-wedged-turn/FINDING.md`) replaced that
    // clause for the approval case: turn completion proves the turn
    // stopped, not that the persistent context discarded its intent.
    //
    // What the original test was protecting is UNCHANGED and still
    // asserted below: nothing is delivered while blocked, and not one
    // retained readiness event is lost.
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-a", status: { type: "inProgress" } });
    fake.emit("serverRequest", approvalRequest());
    for (let index = 1; index <= 3; index += 1) bridge.enqueue(readyEvent("a", index));
    assert.equal(fake.starts.length, 0, "a blocked target took a delivery");
    fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
    await new Promise((resolve) => setTimeout(resolve, 30));
    const status = bridge.handleRequest({ control: "status" });
    assert.equal(status.targets.a.blocked, null,
      "the LIVE block outlived the turn it described");
    assert.equal(status.targets.a.deliverable, false,
      "the quarantined context became deliverable when its turn ended");
    assert.equal(fake.starts.length, 0,
      "a retained event was delivered onto the quarantined context");
    assert.equal(status.targets.a.queueDepth, 3,
      "a retained readiness event was lost rather than held for the "
      + "fresh context a full managed-stack start mints");
    await bridge.stop();
  });

test("W3243: the blocked turn is interrupted within the bound",
  async () => {
    const { bridge, fake } = bridgeWithFake(config({ approvalRecoveryMs: 10 }));
    await bridge.start({ listen: false });
    fake.emit("turnStarted", { threadId: "thread-a", turn: { id: "turn-x" } });
    fake.emit("serverRequest", approvalRequest());
    await new Promise((resolve) => setTimeout(resolve, 40));
    assert.equal(fake.interrupts.length, 1,
      "the turn was left running after the bounded interval");
    assert.equal(fake.interrupts[0].threadId, "thread-a");
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.a.blocked.interrupted,
      true);
    await bridge.stop();
  });

test("W3243 review: recovery uses the approval request's authoritative turn",
  async () => {
    // The app-server schema requires `turnId` on an approval request.
    // The request can race the continuation that records `activeTurn`,
    // so recovery must not replace this exact locator with local state
    // that may still be null.
    const { bridge, fake } = bridgeWithFake(config({ approvalRecoveryMs: 10 }));
    await bridge.start({ listen: false });
    const request = approvalRequest();
    request.params.turnId = "turn-from-request";
    fake.emit("serverRequest", request);
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.a.blocked.turnId,
      "turn-from-request", "status lost the turn named by the request");
    await new Promise((resolve) => setTimeout(resolve, 40));
    assert.equal(fake.interrupts.length, 1);
    assert.equal(fake.interrupts[0].turnId, "turn-from-request",
      "recovery attempted to interrupt a guessed or missing turn");
    await bridge.stop();
  });

test("W3243 review: stopping cancels the pending recovery timer", async () => {
  // stop() owns every timer the bridge starts. A recovery callback must
  // not interrupt through a disconnected client or publish a failure
  // after the runtime has already reported a clean shutdown.
  const { bridge, fake } = bridgeWithFake(config({ approvalRecoveryMs: 10 }));
  await bridge.start({ listen: false });
  const request = approvalRequest();
  request.params.turnId = "turn-stop";
  fake.emit("serverRequest", request);
  await bridge.stop();
  await new Promise((resolve) => setTimeout(resolve, 40));
  assert.equal(fake.interrupts.length, 0,
    "a blocked-turn timer survived bridge shutdown");
});

test("W3243: an interrupt that fails leaves the target visibly unhealthy",
  async () => {
    // No approval, no replacement context, no pretending. The operator
    // restarts the managed stack, whose fresh-context-per-start policy
    // supplies a clean target; v12 owns automatic replacement.
    const { bridge, fake } = bridgeWithFake(config({ approvalRecoveryMs: 10 }));
    fake.interruptFails = true;
    await bridge.start({ listen: false });
    fake.emit("serverRequest", approvalRequest());
    await new Promise((resolve) => setTimeout(resolve, 40));
    const status = bridge.handleRequest({ control: "status" });
    assert.equal(status.ready, false);
    assert.equal(status.targets.a.deliverable, false);
    assert.equal(fake.responses.length, 1, "a retry approved something");
    await bridge.stop();
  });

test("W3243: one target's wedge never delivers its events elsewhere",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    for (const thread of ["thread-a", "thread-b"]) {
      fake.emit("status", { threadId: thread, status: { type: "idle" } });
    }
    fake.emit("serverRequest", approvalRequest("thread-a"));
    bridge.enqueue(readyEvent("a", 1));
    bridge.enqueue(readyEvent("b", 2));
    await new Promise((resolve) => setTimeout(resolve, 30));
    for (const started of fake.starts) {
      assert.notEqual(started.threadId, "thread-a",
        "a wedged target took a delivery");
    }
    assert.ok(fake.starts.some((entry) => entry.threadId === "thread-b"),
      "an unrelated target stopped receiving because another wedged");
    const status = bridge.handleRequest({ control: "status" });
    assert.equal(status.targets.a.queueDepth, 1,
      "the wedged target's event went somewhere else");
    await bridge.stop();
  });

test("W3243: a second request on the same wedge does not restart the clock",
  async () => {
    const { bridge, fake } = bridgeWithFake();
    await bridge.start({ listen: false });
    fake.emit("serverRequest", approvalRequest("thread-a", 7));
    const first = bridge.handleRequest({ control: "status" }).targets.a.blocked.since;
    fake.emit("serverRequest", approvalRequest("thread-a", 8));
    const again = bridge.handleRequest({ control: "status" }).targets.a.blocked.since;
    assert.equal(again, first, "a repeated request reset the recovery bound");
    assert.equal(fake.responses.length, 2, "the second request went unanswered");
    await bridge.stop();
  });

test("W3243: a turn-id disagreement is reported, not silently resolved",
  async () => {
    // Two different turn ids on one thread is a fact an operator needs.
    // The request wins because the schema requires it and local state
    // can still be null — but picking one quietly would hide the
    // disagreement, so it is logged.
    const warnings = [];
    const fake = new FakeClient();
    const bridge = new EventBridge({
      config: config({ approvalRecoveryMs: 10 }),
      logger: { info() {}, warn: (line) => warnings.push(line),
                error() {}, debug() {} },
      clientFactory: () => fake,
    });
    await bridge.start({ listen: false });
    // `activeTurn` is the bridge's record of a turn IT started, so the
    // local side of the disagreement has to come from a real delivery.
    fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
    bridge.enqueue(readyEvent("a", 1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    const request = approvalRequest();
    request.params.turnId = "turn-named";
    fake.emit("serverRequest", request);
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.a.blocked.turnId,
      "turn-named", "local state displaced the turn the request named");
    assert.ok(warnings.some((line) => line.includes("turn-named")
                                   && line.includes("turn-thread-a")),
      `the disagreement was not reported: ${JSON.stringify(warnings)}`);
    await bridge.stop();
  });

test("W3243: a request naming no turn falls back to the recorded one",
  async () => {
    // The schema requires `turnId`, but a bridge that trusted that
    // absolutely would interrupt nothing when a server omitted it.
    const { bridge, fake } = bridgeWithFake(config({ approvalRecoveryMs: 10 }));
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-a", status: { type: "idle" } });
    bridge.enqueue(readyEvent("a", 1));
    await new Promise((resolve) => setTimeout(resolve, 20));
    const request = approvalRequest();
    delete request.params.turnId;
    fake.emit("serverRequest", request);
    await new Promise((resolve) => setTimeout(resolve, 40));
    assert.equal(fake.interrupts.length, 1);
    assert.equal(fake.interrupts[0].turnId, "turn-thread-a");
    await bridge.stop();
  });
