// W99: fence semantic continuation across managed Work turns.
//
// Record: `work/records/2026/08/finding-managed-turn-approval-incidents/`
// Ruling: "Approval-tainted context ruling — confirmed 2026-08-21", with
// the scoped supersession appended to
// `work/records/2026/08/finding-readiness-target-wedged-turn/FINDING.md`.
//
// THE RECURRENCE. The managed `baton.codex` session began W30, requested
// interactive approval to run the v12 suite with Docker access, and the
// dispatcher correctly denied and interrupted that non-interactive turn.
// The next readiness turn was for W28 — and before acting on W28 the same
// persistent context attempted W30's unfinished cleanup,
// `rm -rf /tmp/w30-fixture-audit.Lmr3aa`. The refusal was right both
// times. What was wrong is that a second Work was ever delivered onto a
// context still holding the first Work's intent, and that the incident
// named W28 as the source because correlation read mutable current state.
//
// W3243 recovered the TURN and let the retained events drain once the
// target went idle. Turn completion proves the turn stopped; it does not
// prove the context forgot. So an unexpected approval now QUARANTINES
// that context for the remainder of the managed-stack start, and
// correlation is selected by the approval request's own turn id against
// an immutable delivery attempt.

import { EventEmitter } from "node:events";
import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import { rulesFor } from "../src/exec_policy.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";
import { quarantineKey, QuarantineStore } from "../src/quarantine_store.mjs";

// W415: the dispatcher refuses to start unless the deployment-owned
// execpolicy file authorizes each managed participant's canonical Baton
// operations, so this suite needs a real one.
const FIXTURE_POLICY = join(mkdtempSync("/tmp/w99-fixture-policy-"), "baton.rules");
writeFileSync(FIXTURE_POLICY,
  ["baton.codex", "baton.tuner"]
    .flatMap((participant) => rulesFor({ binary: "/opt/baton/bin/baton",
                                         config: "/home/op/baton.json",
                                         participant }))
    .join("\n") + "\n");

const quiet = { info() {}, warn() {}, error() {}, debug() {} };

class FakeClient extends EventEmitter {
  constructor() {
    super();
    this.connected = true;
    this.starts = [];
    this.responses = [];
    this.interrupts = [];
    this.start = async (threadId) => ({ id: `turn-${threadId}`, status: "inProgress" });
  }

  async connectAndInitialize() {
    this.connected = true;
    this.emit("connected", {});
  }

  respondError(id, code, message) {
    this.responses.push({ id, code, message });
    return true;
  }

  async interruptTurn(threadId, turnId) {
    this.interrupts.push({ threadId, turnId });
    return { ok: true };
  }

  async startTurn(threadId, text, clientId) {
    this.starts.push({ threadId, text, clientId });
    return await this.start(threadId, text, clientId);
  }

  async resume(threadId) {
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

function config({ threadId = "thread-codex", extra = {} } = {}) {
  return validateConfig({
    servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
    targets: {
      codex: { server: "local", threadId,
        identity: { participant: "baton.codex", role: "rview",
                    actionOwner: "ops.slaw" } },
      tuner: { server: "local", threadId: "thread-tuner",
        identity: { participant: "baton.tuner", role: "tuner",
                    actionOwner: "ops.slaw" } },
    },
    roleInstructions: { binary: "/opt/baton/bin/baton",
      config: "/home/op/baton.json", execPolicyFile: FIXTURE_POLICY },
    eventSocket: "/tmp/codex-w99-unused.sock",
    quarantineDir: freshQuarantineDir(),
    approvalRecoveryMs: 10,
    ...extra,
  });
}

/** Every readiness key the participant still owes is live. The fence is
 *  about the CONTEXT, so nothing here may look like a stale episode. */
function alwaysLive() {
  const calls = [];
  return {
    calls,
    revalidate: async (file, args) => {
      calls.push({ file, args });
      const participant = args[args.indexOf("--participant") + 1];
      return { stdout: JSON.stringify({ result: { actionable: [
        { kind: "work", action_key: `work:43c-W30:1:g1`, participant },
        { kind: "work", action_key: `work:43c-W28:1:g1`, participant },
      ] } }) };
    },
  };
}

function dispatcher({ configuration = config(), revalidate,
                      incidentResult = true } = {}) {
  const fake = new FakeClient();
  const published = [];
  const runtime = {
    incarnation: "run-1",
    async start(options) { published.push(["start", options]); },
    async state(state, options) { published.push([state, options]); },
    // Returns a boolean like the real publisher: the durable
    // acknowledgement depends on knowing the report landed.
    async incident(options) {
      published.push(["incident", options]);
      return incidentResult;
    },
    async facts() { return true; },
    async end(options) { published.push(["end", options]); },
  };
  const bridge = new EventBridge({
    config: configuration, logger: quiet, clientFactory: () => fake,
    runtimeFactory: () => runtime,
    revalidate: revalidate ?? alwaysLive().revalidate,
  });
  return { bridge, fake, published };
}

/** A v11 readiness event as the producer actually sends it. */
function workEvent(local, { target = "codex", participant = "baton.codex" } = {}) {
  return {
    target, source: "baton-v11", type: "v11-action-ready",
    summary: `${local} is ready for ${participant}`,
    action: { kind: "work", participant, key: `work:43c-${local}:1:g1`,
              work: `43c-${local}`, localId: local, episode: 1,
              generation: 1, phase: "queued", claimed: false },
  };
}

function approval({ threadId = "thread-codex", id = 7, turnId,
                    method = "item/commandExecution/requestApproval" } = {}) {
  const params = { threadId };
  if (turnId !== undefined) params.turnId = turnId;
  return { id, method, params };
}

async function settle(times = 8) {
  for (let index = 0; index < times; index += 1) {
    await new Promise((resolve) => setImmediate(resolve));
  }
}

async function idleAndReady(bridge, fake) {
  await bridge.start({ listen: false });
  for (const threadId of ["thread-codex", "thread-tuner"]) {
    fake.emit("status", { threadId, status: { type: "idle" } });
  }
  await settle();
}

// -- 1. the attempt survives the race it exists for -------------------------

test("W99: an approval racing turn/start still names the Work it interrupted",
  async () => {
    // The reviewed race: `state.activeTurn` is written by the
    // continuation of `turn/start`, and the approval request can arrive
    // first. Correlating from it filed a locator-less incident while
    // the dispatcher knew exactly which Work it had just delivered.
    const { bridge, fake, published } = dispatcher();
    let release;
    fake.start = async () => await new Promise((resolve) => {
      release = () => resolve({ id: "turn-W30", status: "inProgress" });
    });
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    assert.equal(fake.starts.length, 1, "W30 was never delivered");
    // `turn/start` has NOT returned: nothing local records the turn yet.
    fake.emit("serverRequest", approval({ turnId: "turn-W30" }));
    // The context is fenced IMMEDIATELY — only the Work attribution
    // waits, because until `turn/start` returns this dispatcher cannot
    // prove the named turn is the one it is about to bind. Review round
    // 2 moved this observation past the binding for that reason; the
    // assertions themselves are unchanged.
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
      false, "the fence waited for the attribution");
    release();
    await settle();
    const filed = published.find(([kind]) => kind === "incident");
    assert.ok(filed, `no incident filed: ${JSON.stringify(published)}`);
    assert.equal(filed[1].work, "43c-W30",
      "the incident lost the Work it interrupted to the turn/start race");
    assert.equal(filed[1].episode, 1);
    assert.equal(filed[1].actionKey, "work:43c-W30:1:g1");
    await bridge.stop();
  });

test("W99: a different named turn racing turn/start is not guessed as that Work",
  async () => {
    const { bridge, fake, published } = dispatcher();
    let release;
    fake.start = async () => await new Promise((resolve) => {
      release = () => resolve({ id: "turn-W30", status: "inProgress" });
    });
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    assert.equal(fake.starts.length, 1, "W30 was never delivered");
    fake.emit("serverRequest", approval({ turnId: "turn-somewhere-else" }));
    // Implementer note, review round 2: the assertions below are the
    // reviewer's, unchanged. Only the observation point moved past
    // `release()`, because the correction they asked for — establishing
    // the equality before attaching the attempt — cannot be observed
    // before `turn/start` returns the turn id there is to compare
    // against. The fence is still immediate, asserted here.
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
      false, "the fence waited for the attribution");
    release();
    await settle();
    const filed = published.find(([kind]) => kind === "incident");
    assert.ok(filed, `no incident filed: ${JSON.stringify(published)}`);
    assert.equal(filed[1].work, null,
      "an unmatched request was guessed to belong to the pending Work");
    assert.equal(filed[1].episode, null);
    assert.equal(filed[1].actionKey, null);
    await bridge.stop();
  });

// -- 2. THE fence: no Work-B turn on a Work-A context -----------------------

for (const order of ["completion-then-idle", "idle-then-completion"]) {
  test(`W99: Work B never starts on the context W A was interrupted in (${order})`,
    async () => {
      const { bridge, fake } = dispatcher();
      await idleAndReady(bridge, fake);
      bridge.enqueue(workEvent("W30"));
      await settle();
      assert.deepEqual(fake.starts.map((entry) => entry.threadId), ["thread-codex"]);
      // W30's turn asks for approval to run Docker. Denied, interrupted.
      fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
      await new Promise((resolve) => setTimeout(resolve, 40));
      assert.equal(fake.interrupts.length, 1, "the blocked turn was not ended");
      // W28 arrives while the interrupted context is still loaded.
      assert.equal(bridge.enqueue(workEvent("W28")).accepted, true,
        "the later Work was dropped rather than retained");
      const terminal = [
        () => fake.emit("turnCompleted", { threadId: "thread-codex",
                turn: { id: "turn-thread-codex", status: "interrupted" } }),
        () => fake.emit("status", { threadId: "thread-codex",
                status: { type: "idle" } }),
      ];
      if (order === "idle-then-completion") terminal.reverse();
      for (const emit of terminal) emit();
      await settle();
      await new Promise((resolve) => setTimeout(resolve, 30));
      assert.equal(fake.starts.length, 1,
        "a second turn started on the context that was interrupted mid-Work; "
        + "this is exactly how W30's cleanup ran during W28");
      const target = bridge.handleRequest({ control: "status" }).targets.codex;
      assert.equal(target.deliverable, false);
      assert.equal(target.queueDepth, 1,
        "W28 was neither delivered nor retained");
      await bridge.stop();
    });
}

test("W99: duplicate terminal events do not clear the quarantine", async () => {
  const { bridge, fake } = dispatcher();
  await idleAndReady(bridge, fake);
  bridge.enqueue(workEvent("W30"));
  await settle();
  fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
  bridge.enqueue(workEvent("W28"));
  for (let round = 0; round < 3; round += 1) {
    fake.emit("turnCompleted", { threadId: "thread-codex",
      turn: { id: "turn-thread-codex", status: "interrupted" } });
    fake.emit("status", { threadId: "thread-codex", status: { type: "idle" } });
    await settle();
  }
  await new Promise((resolve) => setTimeout(resolve, 30));
  assert.equal(fake.starts.length, 1,
    "repeating the terminal events eventually shook a delivery loose");
  assert.equal(bridge.handleRequest({ control: "status" }).ready, false);
  await bridge.stop();
});

// -- 3. correlation is selected, never guessed ------------------------------

test("W99: a turn this dispatcher never delivered is reported, not misattributed",
  async () => {
    const warnings = [];
    const fake = new FakeClient();
    const published = [];
    const bridge = new EventBridge({
      config: config(), clientFactory: () => fake,
      logger: { info() {}, warn: (line) => warnings.push(line),
                error() {}, debug() {} },
      runtimeFactory: () => ({
        incarnation: "run-1", async start() {}, async state() {},
        async incident(options) { published.push(options); },
        async facts() { return true; }, async end() {},
      }),
      revalidate: alwaysLive().revalidate,
    });
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-codex", status: { type: "idle" } });
    await settle();
    bridge.enqueue(workEvent("W30"));
    await settle();
    // An approval naming a turn that is not the one delivered. Blaming
    // W30 for it would be a guess, and blaming whatever ran last is the
    // misattribution this Work records.
    fake.emit("serverRequest", approval({ turnId: "turn-somewhere-else" }));
    assert.equal(published.length, 1);
    assert.equal(published[0].work, null,
      "an unmatched approval was attributed to an episode anyway");
    assert.equal(published[0].episode, null);
    assert.equal(published[0].actionKey, null);
    assert.ok(warnings.some((line) => line.includes("turn-somewhere-else")),
      `the unmatched turn was not reported: ${JSON.stringify(warnings)}`);
    // Uncorrelated is not unquarantined: the context is still finished.
    assert.equal(
      bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
      false);
    await bridge.stop();
  });

// -- 4. the operator can tell the two conditions apart ----------------------

test("W99: the row separates live recovery from a terminal quarantine",
  async () => {
    const { bridge, fake } = dispatcher();
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    const during = bridge.handleRequest({ control: "status" }).targets.codex;
    assert.ok(during.blocked, "the live turn condition is not reported");
    assert.ok(during.tainted, "the sticky context condition is not reported");
    assert.equal(during.tainted.cause, "approval");
    assert.equal(during.tainted.category, "shell");
    assert.equal(during.tainted.work, "43c-W30");
    assert.equal(during.tainted.actionKey, "work:43c-W30:1:g1");
    assert.equal(during.tainted.turnId, "turn-thread-codex");
    assert.equal(during.tainted.correlation, "exact");
    // A dispatcher-only restart resumes the SAME configured thread, so
    // the remedy has to say which restart it means.
    assert.match(during.tainted.remedy, /stop and start the managed stack/);
    assert.match(during.tainted.remedy, /fresh context/);

    fake.emit("turnCompleted", { threadId: "thread-codex",
      turn: { id: "turn-thread-codex", status: "interrupted" } });
    await settle();
    const after = bridge.handleRequest({ control: "status" }).targets.codex;
    assert.equal(after.blocked, null, "the live condition outlived its turn");
    assert.ok(after.tainted, "the quarantine was cleared with the live block");
    assert.equal(after.tainted.since, during.tainted.since,
      "the quarantine was re-minted rather than kept");
    assert.equal(after.deliverable, false);
    assert.equal(after.connected, true,
      "connected/loaded must stay distinguishable from quarantined");
    assert.equal(after.loaded, true);
    await bridge.stop();
  });

test("W99: the quarantined runner is published failed, not idle", async () => {
  // An idle-but-undeliverable target published as `idle` is what let
  // the stack look healthy while nothing could reach it.
  const { bridge, fake, published } = dispatcher();
  await idleAndReady(bridge, fake);
  bridge.enqueue(workEvent("W30"));
  await settle();
  fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
  published.length = 0;
  fake.emit("turnCompleted", { threadId: "thread-codex",
    turn: { id: "turn-thread-codex", status: "interrupted" } });
  fake.emit("status", { threadId: "thread-codex", status: { type: "idle" } });
  await settle();
  assert.ok(!published.some(([state]) => state === "idle"),
    `a quarantined context reported itself idle: ${JSON.stringify(published)}`);
  const failures = published.filter(([state]) => state === "failed");
  assert.equal(failures.length, 1,
    "the terminal quarantined state was published once per terminal event");
  assert.equal(failures[0][1].cause, "approval");
  assert.match(failures[0][1].detail, /stop and start the managed stack/);
  await bridge.stop();
});

// -- 5. the fence is per context, not per stack -----------------------------

test("W99: an unrelated target keeps draining, for its own participant",
  async () => {
    const { bridge, fake } = dispatcher();
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    bridge.enqueue(workEvent("W28"));
    bridge.enqueue(workEvent("W28", { target: "tuner", participant: "baton.tuner" }));
    await settle();
    await new Promise((resolve) => setTimeout(resolve, 30));
    const threads = fake.starts.map((entry) => entry.threadId);
    assert.equal(threads.filter((id) => id === "thread-codex").length, 1,
      "the quarantined context took another delivery");
    assert.equal(threads.filter((id) => id === "thread-tuner").length, 1,
      "an unrelated target stopped receiving because another quarantined");
    const status = bridge.handleRequest({ control: "status" });
    assert.equal(status.targets.codex.queueDepth, 1,
      "the quarantined target's Work went somewhere else");
    assert.equal(status.targets.tuner.deliverable, true);
    await bridge.stop();
  });

// -- 6. recovery is a full managed-stack stop/start -------------------------

test("W99: stopping the quarantined bridge cancels its recovery timer",
  async () => {
    const { bridge, fake } = dispatcher();
    await idleAndReady(bridge, fake);
    fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    await bridge.stop();
    await new Promise((resolve) => setTimeout(resolve, 40));
    assert.equal(fake.interrupts.length, 0,
      "a recovery timer survived shutdown and interrupted through a "
      + "disconnected client");
  });

test("W99: a full start with a freshly minted context takes the Work once",
  async () => {
    // The ruled remedy, end to end. The quarantined process holds W28
    // and never delivers it; the stack is stopped and started, which
    // mints a NEW thread id, and Baton's level-triggered readiness
    // re-offers the still-actionable W28 to that fresh context exactly
    // once.
    const first = dispatcher();
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    first.bridge.enqueue(workEvent("W28"));
    await settle();
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.equal(first.fake.starts.length, 1, "W28 ran on the tainted context");
    await first.bridge.stop();

    const answer = alwaysLive();
    const fresh = dispatcher({
      configuration: config({ threadId: "thread-codex-2" }),
      revalidate: answer.revalidate,
    });
    await fresh.bridge.start({ listen: false });
    fresh.fake.emit("status", { threadId: "thread-codex-2", status: { type: "idle" } });
    await settle();
    fresh.bridge.enqueue(workEvent("W28"));
    await settle();
    await new Promise((resolve) => setTimeout(resolve, 30));
    assert.deepEqual(fresh.fake.starts.map((entry) => entry.threadId),
      ["thread-codex-2"],
      "the fresh context did not take the retained Work exactly once");
    assert.ok(answer.calls.some((call) =>
      call.args.includes("baton.codex") && call.args.includes("wait")),
      "the fresh delivery skipped canonical revalidation");
    assert.equal(fresh.bridge.handleRequest({ control: "status" }).ready, true,
      "the fresh stack did not report healthy");
    await fresh.bridge.stop();
  });

test("W99: restarting only the dispatcher does not clear the quarantine",
  async () => {
    // A dispatcher process can be stopped and relaunched against the same
    // rendered configuration. That is not a managed-stack start: it resumes
    // the same context and therefore must not make this thread deliverable.
    // Implementer note, review round 2: ONE configuration object drives
    // both processes. "The same rendered configuration" is the premise
    // of the test, and calling the helper twice minted two different
    // dispatcher runtime directories — two deployments, not a restart.
    const rendered = config();
    const first = dispatcher({ configuration: rendered });
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    await settle();
    await first.bridge.stop();

    const restarted = dispatcher({ configuration: rendered });
    await idleAndReady(restarted.bridge, restarted.fake);
    restarted.bridge.enqueue(workEvent("W28"));
    await settle();
    assert.equal(restarted.fake.starts.length, 0,
      "a dispatcher-only restart cleared the fence and delivered Work on "
      + "the same approval-tainted context");
    assert.equal(
      restarted.bridge.handleRequest({ control: "status" }).targets.codex
        .deliverable,
      false);
    await restarted.bridge.stop();
  });

// -- review round 2: the durable fence and the bounded attribution ---------

test("W99: a fresh managed context is not fenced by the old context's marker",
  async () => {
    // The whole reason the marker is keyed by server+thread: a full
    // managed-stack start MINTS a new thread id, so the previous
    // context's quarantine is simply not this context's. Nothing has to
    // delete it, and nothing may inherit it.
    const rendered = config();
    const first = dispatcher({ configuration: rendered });
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    await settle();
    await first.bridge.stop();
    assert.equal(
      new QuarantineStore(rendered.quarantineDir, quiet).keys().length, 1,
      "the quarantine was never persisted");

    const fresh = dispatcher({ configuration: config({
      threadId: "thread-codex-2", extra: { quarantineDir: rendered.quarantineDir } }) });
    await fresh.bridge.start({ listen: false });
    fresh.fake.emit("status", { threadId: "thread-codex-2", status: { type: "idle" } });
    await settle();
    const target = fresh.bridge.handleRequest({ control: "status" }).targets.codex;
    assert.equal(target.tainted, null,
      "a freshly minted context inherited the old context's quarantine");
    assert.equal(target.deliverable, true);
    await fresh.bridge.stop();
  });

test("W99: a malformed marker never makes its context deliverable",
  async () => {
    // A marker at this exact context key is positive evidence that a
    // quarantine was recorded. If its payload is damaged, the bridge no
    // longer knows the diagnostic fields, but it must not turn that loss of
    // evidence into proof that the persistent context is clean. Refusing
    // startup or loading an unknown-but-tainted row are both safe outcomes.
    const rendered = config();
    const marker = join(rendered.quarantineDir,
      `${quarantineKey("local", "thread-codex")}.json`);
    writeFileSync(marker, "{this is not valid JSON\n", { mode: 0o600 });
    const { bridge, fake } = dispatcher({ configuration: rendered });
    let started = false;
    let startupError = null;
    try {
      await bridge.start({ listen: false });
      started = true;
    } catch (error) {
      startupError = error;
    }
    if (startupError) {
      assert.match(startupError.message, /quarantine|marker/i,
        "startup failed for a reason unrelated to the damaged fence");
      return;
    }
    try {
      fake.emit("status", {
        threadId: "thread-codex", status: { type: "idle" },
      });
      await settle();
      bridge.enqueue(workEvent("W28"));
      await settle();
      assert.equal(fake.starts.length, 0,
        "a malformed quarantine marker was treated as a clean context");
      assert.equal(
        bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
        false);
    } finally {
      if (started) await bridge.stop();
    }
  });

test("W99: an out-of-range marker instant stays isolated to its context",
  async () => {
    // `Number.isFinite` is not enough to make a value a usable JavaScript
    // instant. Restoration logs `new Date(since).toISOString()`, so a finite
    // value outside Date's range must be classified as damaged rather than
    // aborting startup for every otherwise healthy target.
    const rendered = config();
    new QuarantineStore(rendered.quarantineDir, quiet).save(
      "local", "thread-codex", { since: Number.MAX_VALUE });
    const { bridge, fake } = dispatcher({ configuration: rendered });
    await bridge.start({ listen: false });
    try {
      for (const threadId of ["thread-codex", "thread-tuner"]) {
        fake.emit("status", { threadId, status: { type: "idle" } });
      }
      await settle();
      const status = bridge.handleRequest({ control: "status" });
      assert.equal(status.targets.codex.deliverable, false,
        "the damaged context was treated as clean");
      assert.equal(status.targets.tuner.deliverable, true,
        "one damaged marker took down an unrelated target");
    } finally {
      await bridge.stop();
    }
  });

test("W99: the persisted marker carries no command body, argv or environment",
  async () => {
    const rendered = config();
    const { bridge, fake } = dispatcher({ configuration: rendered });
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", {
      id: 9, method: "item/commandExecution/requestApproval",
      params: {
        threadId: "thread-codex", turnId: "turn-thread-codex",
        command: ["/bin/bash", "-lc", "rm -rf /tmp/w30-fixture-audit.Lmr3aa"],
        cwd: "/home/sl/src/baton",
        env: { ANTHROPIC_API_KEY: "sk-ant-secret-value" },
      },
    });
    await settle();
    const store = new QuarantineStore(rendered.quarantineDir, quiet);
    // Round 3 gave `load` a three-way answer — absent, present, damaged —
    // because reading a damaged marker as absent failed open.
    const found = store.load("local", "thread-codex");
    assert.equal(found.state, "present", "nothing well-formed was persisted");
    const record = found.record;
    assert.equal(record.work, "43c-W30", "the marker lost its correlation");
    const serialized = JSON.stringify(record);
    for (const leaked of ["/bin/bash", "-lc", "rm -rf", "w30-fixture-audit",
                          "sk-ant", "ANTHROPIC", "/home/sl/src/baton"]) {
      assert.ok(!serialized.includes(leaked),
        `the persisted marker leaked ${leaked}: ${serialized}`);
    }
    // Live-only bookkeeping stays out of the durable record. Round 3
    // moved exactly one field the other way: `incidentFiled` MUST be
    // durable, because a restore cannot otherwise tell a published
    // incident from a process that died before publishing one.
    for (const live of ["reported", "restored", "durable"]) {
      assert.ok(!(live in record), `the marker persisted live field ${live}`);
    }
    assert.equal(record.incidentFiled, true,
      "the incident acknowledgement was not made durable");
    await bridge.stop();
  });

test("W99: a fence that cannot be persisted says so instead of implying durability",
  async () => {
    // A marker directory that cannot be created is a real deployment
    // fault. The in-process fence still holds, and the row must not
    // claim a durability the operator does not have — otherwise they
    // relaunch the dispatcher believing the fence survives.
    const blocked = join(freshQuarantineDir(), "not-a-directory");
    writeFileSync(blocked, "");
    const { bridge, fake } = dispatcher({ configuration: config({
      extra: { quarantineDir: join(blocked, "quarantine") } }) });
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    const target = bridge.handleRequest({ control: "status" }).targets.codex;
    assert.ok(target.tainted, "the in-process fence was lost with the marker");
    assert.equal(target.deliverable, false);
    assert.equal(target.tainted.durable, false,
      "a fence that was never written reported itself durable");
    await bridge.stop();
  });

test("W99: an attribution that can never be proven is still filed, uncorrelated",
  async () => {
    // The settlement bound. A quarantined target never drains again, so
    // a deferred attribution with no settlement point would silently
    // lose the operator's one durable notice of the failure.
    const { bridge, fake, published } = dispatcher();
    let reject;
    fake.start = async () => await new Promise((_resolve, no) => { reject = no; });
    await idleAndReady(bridge, fake);
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", approval({ turnId: "turn-W30" }));
    assert.equal(published.filter(([kind]) => kind === "incident").length, 0,
      "the attribution was published before it could be proven");
    reject(new Error("the app-server dropped the connection"));
    await settle();
    const filed = published.find(([kind]) => kind === "incident");
    assert.ok(filed, "a deferred incident was never filed at all");
    assert.equal(filed[1].work, null,
      "a turn that never bound was still credited with the Work");
    assert.equal(filed[1].actionKey, null);
    await bridge.stop();
  });

test("W99: an acknowledged incident is not re-filed on every restart",
  async () => {
    // The other half of the acknowledgement. Recovering a possibly-lost
    // incident is only safe if a durable "this one landed" record stops
    // it becoming a fresh report on every relaunch.
    const rendered = config();
    const first = dispatcher({ configuration: rendered });
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    await settle();
    assert.equal(first.published.filter(([kind]) => kind === "incident").length, 1);
    await first.bridge.stop();

    for (let relaunch = 0; relaunch < 3; relaunch += 1) {
      const again = dispatcher({ configuration: rendered });
      await idleAndReady(again.bridge, again.fake);
      assert.equal(again.published.filter(([kind]) => kind === "incident").length, 0,
        `relaunch ${relaunch} re-filed an incident that was already recorded`);
      assert.equal(
        again.bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
        false, "a relaunch cleared the fence");
      await again.bridge.stop();
    }
  });

test("W99: restart cannot lose an incident whose attribution was pending",
  async () => {
    // The marker is committed before denial, while the incident waits for
    // `turn/start` to bind. A dispatcher can stop in that window. Either the
    // stopping process must settle the incident or the restoring process must
    // recover it as uncorrelated; restoration cannot assume it was filed.
    const rendered = config();
    const first = dispatcher({ configuration: rendered });
    first.fake.start = async () => await new Promise(() => {});
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-W30" }));
    await settle();
    assert.equal(
      first.published.filter(([kind]) => kind === "incident").length, 0,
      "the fixture did not reach the deferred-attribution window");
    await first.bridge.stop();

    const restarted = dispatcher({ configuration: rendered });
    await idleAndReady(restarted.bridge, restarted.fake);
    const incidents = [...first.published, ...restarted.published]
      .filter(([kind]) => kind === "incident");
    assert.equal(incidents.length, 1,
      "the persisted pending quarantine lost its durable incident on restart");
    assert.equal(incidents[0][1].work, null);
    assert.equal(incidents[0][1].actionKey, null);
    assert.equal(
      restarted.bridge.handleRequest({ control: "status" }).targets.codex
        .deliverable,
      false);
    await restarted.bridge.stop();
  });

test("W99: restart retains an unpublished incident's proven Work origin",
  async () => {
    // Unlike a pending origin, an exact marker already contains the result of
    // matching the request's authoritative turn id to an immutable delivery
    // attempt. Losing the process does not invalidate that durable proof.
    const rendered = config();
    const first = dispatcher({ configuration: rendered, incidentResult: false });
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: "turn-thread-codex" }));
    await settle();
    assert.equal(first.published.filter(([kind]) => kind === "incident").length, 1,
      "the fixture did not attempt the first incident publication");
    const marker = new QuarantineStore(rendered.quarantineDir, quiet)
      .load("local", "thread-codex");
    assert.equal(marker.state, "present");
    assert.equal(marker.record.correlation, "exact");
    assert.equal(marker.record.incidentFiled, false);
    await first.bridge.stop();

    const restarted = dispatcher({ configuration: rendered });
    await idleAndReady(restarted.bridge, restarted.fake);
    const recovered = restarted.published.find(([kind]) => kind === "incident");
    assert.ok(recovered, "the unpublished incident was not recovered");
    assert.equal(recovered[1].work, "43c-W30",
      "restart discarded an origin that the durable marker had already proven");
    assert.equal(recovered[1].episode, 1);
    assert.equal(recovered[1].actionKey, "work:43c-W30:1:g1");
    await restarted.bridge.stop();
  });

test("W99 review: recovery does not invent a stricter turn-id contract",
  async () => {
    // The app-server schema types a turn id as a string, while the live
    // bridge binds any non-empty string verbatim. If that exact value later
    // arrives on the approval request, the live path proves the origin and
    // persists it as `exact`. Recovery cannot retroactively apply the
    // action-locator trimming contract to this separate opaque identifier
    // and discard proof the dispatcher itself produced. If padded turn ids
    // are to be refused, that must happen on the live binding path too.
    const rendered = config();
    const first = dispatcher({ configuration: rendered, incidentResult: false });
    first.fake.start = async () => ({
      id: " turn-thread-codex ", status: "inProgress",
    });
    await idleAndReady(first.bridge, first.fake);
    first.bridge.enqueue(workEvent("W30"));
    await settle();
    first.fake.emit("serverRequest", approval({ turnId: " turn-thread-codex " }));
    await settle();
    const marker = new QuarantineStore(rendered.quarantineDir, quiet)
      .load("local", "thread-codex");
    assert.equal(marker.state, "present");
    assert.equal(marker.record.correlation, "exact");
    assert.equal(marker.record.turnId, " turn-thread-codex ");
    assert.equal(marker.record.incidentFiled, false);
    await first.bridge.stop();

    const restarted = dispatcher({ configuration: rendered });
    await idleAndReady(restarted.bridge, restarted.fake);
    const recovered = restarted.published.find(([kind]) => kind === "incident");
    assert.ok(recovered, "the unpublished incident was not recovered");
    assert.equal(recovered[1].work, "43c-W30",
      "restart discarded an origin the live path had already proven");
    assert.equal(recovered[1].episode, 1);
    assert.equal(recovered[1].actionKey, "work:43c-W30:1:g1");
    await restarted.bridge.stop();
  });

test("W99: recovery reconstructs an origin only from a marker that proved one",
  async () => {
    // The other half of round 4. `exact` is the ONLY correlation that
    // carries proof; every other restored marker must still file
    // uncorrelated, and a locator that is not fully well-formed is not
    // proof of anything — a partially written or hand-edited marker must
    // not inject a Work locator the dispatcher never derived.
    const proven = {
      since: 1, cause: "approval", category: "shell",
      method: "item/commandExecution/requestApproval",
      turnId: "turn-thread-codex", correlation: "exact",
      work: "43c-W30", episode: 1, actionKey: "work:43c-W30:1:g1",
      requests: 1, incidentFiled: false, remedy: "stop and start the stack",
    };
    const cases = [
      ["exact and well-formed", proven, "43c-W30"],
      ["pending was never settled", { ...proven, correlation: "pending" }, null],
      ["unmatched was settled against it", { ...proven, correlation: "unmatched" }, null],
      ["unknown lost its payload", { ...proven, correlation: "unknown" }, null],
      ["no proving turn id", { ...proven, turnId: null }, null],
      ["no work", { ...proven, work: null }, null],
      ["no episode", { ...proven, episode: null }, null],
      ["fractional episode", { ...proven, episode: 1.5 }, null],
      ["no action key", { ...proven, actionKey: "" }, null],
    ];
    for (const [label, record, expected] of cases) {
      const rendered = config();
      new QuarantineStore(rendered.quarantineDir, quiet)
        .save("local", "thread-codex", record);
      const { bridge, published } = dispatcher({ configuration: rendered });
      await bridge.start({ listen: false });
      await settle();
      const filed = published.find(([kind]) => kind === "incident");
      assert.ok(filed, `${label}: the recovery incident was not filed`);
      assert.equal(filed[1].work, expected, `${label}: wrong Work origin`);
      if (expected === null) {
        assert.equal(filed[1].episode, null, `${label}: leaked an episode`);
        assert.equal(filed[1].actionKey, null, `${label}: leaked an action key`);
      } else {
        assert.equal(filed[1].episode, 1, `${label}: lost the proven episode`);
        assert.equal(filed[1].actionKey, "work:43c-W30:1:g1",
          `${label}: lost the proven action key`);
      }
      assert.equal(
        bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
        false, `${label}: the restored marker did not fence the context`);
      await bridge.stop();
    }
  });

test("W99: recovered locator text satisfies the live action contract",
  async () => {
    const base = {
      since: 1, cause: "approval", category: "shell",
      method: "item/commandExecution/requestApproval",
      turnId: "turn-thread-codex", correlation: "exact",
      work: "43c-W30", episode: 1, actionKey: "work:43c-W30:1:g1",
      requests: 1, incidentFiled: false, remedy: "stop and start the stack",
    };
    for (const [label, record] of [
      ["blank work", { ...base, work: "   " }],
      ["blank action key", { ...base, actionKey: "   " }],
    ]) {
      const rendered = config();
      new QuarantineStore(rendered.quarantineDir, quiet)
        .save("local", "thread-codex", record);
      const { bridge, published } = dispatcher({ configuration: rendered });
      await bridge.start({ listen: false });
      await settle();
      const filed = published.find(([kind]) => kind === "incident");
      assert.ok(filed, `${label}: the recovery incident was not filed`);
      assert.equal(filed[1].work, null, `${label}: injected a Work origin`);
      assert.equal(filed[1].episode, null, `${label}: injected an episode`);
      assert.equal(filed[1].actionKey, null, `${label}: injected an action key`);
      await bridge.stop();
    }
  });

test("W99: recovery refuses locator text the live path would have trimmed",
  async () => {
    // Beyond the review's blank-text ask, and for the same reason.
    // `normalizeAction` stores the TRIMMED form, so a marker holding
    // action-locator text that still needs trimming did not come from the
    // live path. Repairing it here would be the dispatcher accepting a
    // locator it never derived; padded text is refused rather than silently
    // normalized.
    //
    // Round-6 correction: this contract covers `work` and `actionKey` only.
    // A padded TURN ID is a value the live binding accepts verbatim and
    // proves by exact equality, so it is covered by the positive case below
    // and by the review's own live-path regression — this round removed the
    // `padded turn id` case that wrongly asserted the opposite, and narrowed
    // its `blank` case to the EMPTY string, which is the only turn id the
    // live binding itself refuses.
    const base = {
      since: 1, cause: "approval", category: "shell",
      method: "item/commandExecution/requestApproval",
      turnId: "turn-thread-codex", correlation: "exact",
      work: "43c-W30", episode: 1, actionKey: "work:43c-W30:1:g1",
      requests: 1, incidentFiled: false, remedy: "stop and start the stack",
    };
    for (const [label, record] of [
      ["padded work", { ...base, work: " 43c-W30 " }],
      ["padded action key", { ...base, actionKey: "work:43c-W30:1:g1\n" }],
      ["empty turn id", { ...base, turnId: "" }],
    ]) {
      const rendered = config();
      new QuarantineStore(rendered.quarantineDir, quiet)
        .save("local", "thread-codex", record);
      const { bridge, published } = dispatcher({ configuration: rendered });
      await bridge.start({ listen: false });
      await settle();
      const filed = published.find(([kind]) => kind === "incident");
      assert.ok(filed, `${label}: the recovery incident was not filed`);
      assert.equal(filed[1].work, null, `${label}: injected a Work origin`);
      assert.equal(filed[1].episode, null, `${label}: injected an episode`);
      assert.equal(filed[1].actionKey, null, `${label}: injected an action key`);
      assert.equal(
        bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
        false, `${label}: the restored marker did not fence the context`);
      await bridge.stop();
    }
  });

test("W99: an opaque turn id keeps whatever shape the live path bound",
  async () => {
    // The other side of the round-6 boundary, at the marker level. The turn
    // id is proved by exact equality against the value `turn/start`
    // returned, so its shape is identity rather than damage — while the
    // action-locator text beside it still has to satisfy the live
    // normalizer's contract. The two predicates are different on purpose.
    const base = {
      since: 1, cause: "approval", category: "shell",
      method: "item/commandExecution/requestApproval",
      correlation: "exact", work: "43c-W30", episode: 1,
      actionKey: "work:43c-W30:1:g1", requests: 1, incidentFiled: false,
      remedy: "stop and start the stack",
    };
    for (const turnId of [" turn-thread-codex ", "turn\nthread", "  "]) {
      const rendered = config();
      new QuarantineStore(rendered.quarantineDir, quiet)
        .save("local", "thread-codex", { ...base, turnId });
      const { bridge, published } = dispatcher({ configuration: rendered });
      await bridge.start({ listen: false });
      await settle();
      const filed = published.find(([kind]) => kind === "incident");
      assert.ok(filed, `${JSON.stringify(turnId)}: no recovery incident`);
      assert.equal(filed[1].work, "43c-W30",
        `${JSON.stringify(turnId)}: recovery applied a contract the live `
        + `binding does not enforce`);
      assert.equal(filed[1].actionKey, "work:43c-W30:1:g1");
      await bridge.stop();
    }
  });

test("W99: an unreadable marker instant is repaired, not rethrown every start",
  async () => {
    // Classifying the out-of-range instant as damaged is only half of it:
    // the damaged bytes are copied aside and a well-formed
    // unknown-but-tainted record takes their place, so the SECOND restart
    // reads a marker it can format instead of meeting the same value again.
    const rendered = config();
    const marker = join(rendered.quarantineDir,
      `${quarantineKey("local", "thread-codex")}.json`);
    new QuarantineStore(rendered.quarantineDir, quiet).save(
      "local", "thread-codex", { since: Number.MAX_VALUE });

    for (const pass of ["first", "second"]) {
      const { bridge } = dispatcher({ configuration: rendered });
      await bridge.start({ listen: false });
      await settle();
      assert.equal(
        bridge.handleRequest({ control: "status" }).targets.codex.deliverable,
        false, `${pass} start: the damaged context was treated as clean`);
      await bridge.stop();
    }
    assert.equal(
      new QuarantineStore(rendered.quarantineDir, quiet)
        .load("local", "thread-codex").state,
      "present", "the unreadable instant was never replaced");
    assert.equal(
      JSON.parse(readFileSync(`${marker}.damaged`, "utf8")).since,
      Number.MAX_VALUE, "the damaged bytes were not preserved for inspection");
  });

// -- the payload boundary the ruling keeps ----------------------------------

test("W99: quarantine diagnostics carry no command body, argv or environment",
  async () => {
    const lines = [];
    const fake = new FakeClient();
    const published = [];
    const bridge = new EventBridge({
      config: config(), clientFactory: () => fake,
      logger: { info: (line) => lines.push(line), warn: (line) => lines.push(line),
                error: (line) => lines.push(line), debug() {} },
      runtimeFactory: () => ({
        incarnation: "run-1", async start() {}, async state(s, o) { published.push([s, o]); },
        async incident(options) { published.push(["incident", options]); },
        async facts() { return true; }, async end() {},
      }),
      revalidate: alwaysLive().revalidate,
    });
    await bridge.start({ listen: false });
    fake.emit("status", { threadId: "thread-codex", status: { type: "idle" } });
    await settle();
    bridge.enqueue(workEvent("W30"));
    await settle();
    fake.emit("serverRequest", {
      id: 9, method: "item/commandExecution/requestApproval",
      params: {
        threadId: "thread-codex", turnId: "turn-thread-codex",
        command: ["/bin/bash", "-lc", "rm -rf /tmp/w30-fixture-audit.Lmr3aa"],
        cwd: "/home/sl/src/baton",
        env: { ANTHROPIC_API_KEY: "sk-ant-secret-value" },
      },
    });
    await settle();
    const status = bridge.handleRequest({ control: "status" });
    const serialized = JSON.stringify([published, lines, status]);
    for (const leaked of ["/bin/bash", "-lc", "rm -rf", "w30-fixture-audit",
                          "sk-ant", "ANTHROPIC", "/home/sl/src/baton"]) {
      assert.ok(!serialized.includes(leaked),
        `the quarantine diagnostics leaked ${leaked}`);
    }
    await bridge.stop();
  });
