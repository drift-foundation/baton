// W148: focused Node coverage for the standalone v11 readiness
// producer — every acceptance case named in the finding, with the v10
// adapter suite untouched beside it.

import test from "node:test";
import assert from "node:assert/strict";
import { actionEvent, actionLocator, codexBatonBridge, validateEnvelope } from "../src/codex_baton_bridge.mjs";

const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

function envelope(actions, { timedOut = false, participant = "baton.codex", uuid = UUID, projection = "4.3" } = {}) {
  return {
    protocol_version: 11,
    projection_version: projection,
    participant,
    authority_uuid: uuid,
    snapshot_seq: 42,
    result: { actionable: actions, timed_out: timedOut },
  };
}

function workAction(id, { claimed = false, title = "t" } = {}) {
  return { kind: "work", action_key: `work:${id}`, work: id, local_id: id.split("-").pop(), title, phase: "queued", claimed };
}

function obligationAction(seq, work) {
  return { kind: "obligation", action_key: `obligation:${seq}`, seq, work, flavor: "response" };
}

function roundAction(work, round, generation) {
  return {
    kind: "due_round",
    action_key: `round:${work}:${round}:${generation}`,
    work,
    round,
    deadline_generation: generation,
    review_at: "2026-08-16T12:00:00Z",
  };
}

function harness(script, options = {}) {
  const events = [];
  const controller = new AbortController();
  let calls = 0;
  const run = codexBatonBridge({ participant: "baton.codex", target: "baton", "retry-ms": "1", ...options }, {
    signal: controller.signal,
    runWait: async () => {
      if (calls >= script.length) {
        controller.abort();
        const error = new Error("aborted");
        error.name = "AbortError";
        throw error;
      }
      const step = script[calls];
      calls += 1;
      return typeof step === "function" ? step() : step;
    },
    emitEvent: async (_socket, event) => {
      events.push(event);
      const respond = options.respond ?? (() => ({ accepted: true }));
      return respond(event);
    },
    logger: { info() {}, warn() {} },
  });
  return { run, events, controller };
}

test("multiple simultaneous action keys each emit one scoped event", async () => {
  const actions = [
    obligationAction(9, "7ba67cb8-W2"),
    roundAction("7ba67cb8-W3", 1, 1),
    workAction("7ba67cb8-W5"),
  ];
  const { run, events } = harness([envelope(actions)]);
  await run;
  assert.equal(events.length, 3);
  assert.deepEqual(events.map((event) => event.id), [
    `baton-v11:${UUID}:baton.codex:obligation:9`,
    `baton-v11:${UUID}:baton.codex:round:7ba67cb8-W3:1:1`,
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5`,
  ]);
  for (const event of events) {
    assert.equal(event.source, "baton-v11");
    assert.equal(event.type, "v11-action-ready");
    assert.match(event.summary, /canonical v11 CLI/);
    assert.doesNotMatch(event.details, /body/);
  }
});

test("a persistent set is level-triggered: suppressed while present, no busy loop", async () => {
  const set = [workAction("7ba67cb8-W5")];
  const { run, events } = harness([envelope(set), envelope(set), envelope(set)]);
  await run;
  assert.equal(events.length, 1, "a persistent key re-emitted");
});

test("claiming the same Work does not duplicate its wake", async () => {
  const { run, events } = harness([
    envelope([workAction("7ba67cb8-W5")]),
    envelope([workAction("7ba67cb8-W5", { claimed: true })]),
  ]);
  await run;
  assert.equal(events.length, 1, "the claim manufactured a second event");
});

test("disappearance forgets the key and reappearance emits it again", async () => {
  const { run, events } = harness([
    envelope([workAction("7ba67cb8-W5")]),
    envelope([], { timedOut: true }),
    envelope([workAction("7ba67cb8-W5")]),
  ]);
  await run;
  assert.equal(events.length, 2, "a returned action did not wake again");
  assert.equal(events[0].id, events[1].id);
});

test("a new obligation key and a new deadline generation are new wakes", async () => {
  const { run, events } = harness([
    envelope([obligationAction(9, "7ba67cb8-W2"), roundAction("7ba67cb8-W3", 1, 1)]),
    envelope([obligationAction(12, "7ba67cb8-W2"), roundAction("7ba67cb8-W3", 1, 2)]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.id.split(":").slice(2).join(":")), [
    "baton.codex:obligation:9",
    "baton.codex:round:7ba67cb8-W3:1:1",
    "baton.codex:obligation:12",
    "baton.codex:round:7ba67cb8-W3:1:2",
  ]);
});

test("a restarted monitor rediscovers the current set", async () => {
  const set = [workAction("7ba67cb8-W5"), obligationAction(9, "7ba67cb8-W2")];
  const first = harness([envelope(set)]);
  await first.run;
  assert.equal(first.events.length, 2);
  // a fresh process: empty memory, same authority state
  const second = harness([envelope(set)]);
  await second.run;
  assert.equal(second.events.length, 2, "restart lost the current set");
  assert.deepEqual(second.events.map((e) => e.id), first.events.map((e) => e.id));
});

test("malformed and wrong-protocol output refuse instead of guessing", async () => {
  const bad = [
    { ready: true, channel: "message", message_id: "abc" },        // a v10 shape
    { ...envelope([]), protocol_version: 10 },
    envelope([], { participant: "someone.else" }),
    { ...envelope([]), result: {} },
    envelope([{ kind: "work", action_key: "work:x" }]),
  ];
  const warnings = [];
  const controller = new AbortController();
  let calls = 0;
  await codexBatonBridge({ participant: "baton.codex", target: "baton", "retry-ms": "1" }, {
    signal: controller.signal,
    runWait: async () => {
      if (calls >= bad.length) {
        controller.abort();
        const error = new Error("aborted");
        error.name = "AbortError";
        throw error;
      }
      return bad[calls++];
    },
    emitEvent: async () => { throw new Error("must never emit for refused output"); },
    logger: { info() {}, warn(message) { warnings.push(message); } },
  });
  assert.equal(warnings.length, bad.length);
  assert.match(warnings[0], /protocol-11/);
  assert.match(warnings[1], /protocol-11/);
  assert.match(warnings[2], /participant/);
  assert.match(warnings[3], /actionable/);
  assert.match(warnings[4], /names no Work/);
});

test("forwarding retry does not lose a key", async () => {
  let rejected = false;
  const set = [workAction("7ba67cb8-W5")];
  const { run, events } = harness([envelope(set), envelope(set)], {
    respond: () => {
      if (!rejected) {
        rejected = true;
        return { accepted: false, reason: "socket closed" };
      }
      return { accepted: true };
    },
  });
  await run;
  assert.equal(events.length, 2, "the failed forward was not retried");
  assert.equal(events[0].id, events[1].id);
  // the bridge's own duplicate answer counts as delivered
  const dupe = harness([envelope(set), envelope(set)], {
    respond: () => ({ accepted: false, reason: "duplicate" }),
  });
  await dupe.run;
  assert.equal(dupe.events.length, 1, "a duplicate answer re-sent the key");
});

test("--once exits after the first accepted event", async () => {
  const { run, events } = harness(
    [envelope([workAction("7ba67cb8-W5")]), envelope([workAction("7ba67cb8-W9")])],
    { once: true },
  );
  const code = await run;
  assert.equal(code, 0);
  assert.equal(events.length, 1);
});

test("the locator carries stable identities and never a body", () => {
  const round = actionLocator(roundAction("7ba67cb8-W3", 2, 5));
  assert.deepEqual(round, {
    kind: "due_round",
    action_key: "round:7ba67cb8-W3:2:5",
    work: "7ba67cb8-W3",
    round: 2,
    deadline_generation: 5,
    review_at: "2026-08-16T12:00:00Z",
  });
  const obligation = actionLocator(obligationAction(9, "7ba67cb8-W2"));
  assert.deepEqual(obligation, {
    kind: "obligation",
    action_key: "obligation:9",
    work: "7ba67cb8-W2",
    obligation_seq: 9,
    flavor: "response",
  });
  const event = actionEvent(envelope([]), workAction("7ba67cb8-W5"), { target: "baton" });
  assert.equal(event.id, `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5`);
  assert.equal(validateEnvelope(envelope([]), "baton.codex").protocol_version, 11);
});

// ---- W148 round 2 ----

test("an authority switch emits the new action while retiring the old set", async () => {
  const OTHER = "9f21aa04c2e94b7fb1b3d7bb64ab0f10";
  const { run, events } = harness([
    envelope([workAction("7ba67cb8-W5")]),
    // the SAME action key under a NEW authority: a genuinely new wake
    envelope([workAction("7ba67cb8-W5")], { uuid: OTHER }),
    // and the old authority's memory is retired, not lingering: coming
    // back to it re-emits rather than staying suppressed
    envelope([workAction("7ba67cb8-W5")]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.id), [
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5`,
    `baton-v11:${OTHER}:baton.codex:work:7ba67cb8-W5`,
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5`,
  ]);
});

test("the typed contract refuses every inconsistent envelope by name", () => {
  const cases = [
    // incompatible projection: older 4.x, other major, missing
    [envelope([], { projection: "4.2" }), /4\.3 participant-action contract/],
    [envelope([], { projection: "5.0" }), /4\.3 participant-action contract/],
    [{ ...envelope([]), projection_version: undefined }, /4\.3 participant-action contract/],
    // missing snapshot token / non-boolean timed_out
    [{ ...envelope([]), snapshot_seq: "42" }, /snapshot_seq/],
    [{ ...envelope([]), result: { actionable: [], timed_out: "no" } }, /timed_out is not a boolean/],
    // contradictory timeout: timed out yet carrying actions
    [envelope([workAction("7ba67cb8-W5")], { timedOut: true }), /contradictory/],
    // unknown kind
    [envelope([{ kind: "message", action_key: "message:9" }]), /unknown action kind "message"/],
    // malformed per-kind payloads
    [envelope([{ kind: "work", action_key: "work:7ba67cb8-W5" }]), /names no Work/],
    [envelope([{ kind: "obligation", action_key: "obligation:9", work: "7ba67cb8-W2" }]), /has no positive seq/],
    [envelope([{ kind: "due_round", action_key: "round:7ba67cb8-W3:1:1", work: "7ba67cb8-W3", round: 1 }]), /lacks its positive work\/round\/generation locator/],
    // key/field disagreement, one per kind
    [envelope([{ ...workAction("7ba67cb8-W5"), action_key: "work:7ba67cb8-W9" }]), /disagrees with work/],
    [envelope([{ ...obligationAction(9, "7ba67cb8-W2"), action_key: "obligation:12" }]), /disagrees with seq/],
    [envelope([{ ...roundAction("7ba67cb8-W3", 1, 1), action_key: "round:7ba67cb8-W3:1:2" }]), /disagrees with its locator/],
    // duplicate action key
    [envelope([workAction("7ba67cb8-W5"), workAction("7ba67cb8-W5")]), /duplicate action_key/],
  ];
  for (const [payload, pattern] of cases) {
    assert.throws(() => validateEnvelope(payload, "baton.codex"), pattern);
  }
  // and the boundary the gate is FOR: a later 4.x minor stays accepted
  assert.equal(validateEnvelope(envelope([], { projection: "4.7" }), "baton.codex").snapshot_seq, 42);
});

test("every field the trusted summary consumes is typed and agreeing", () => {
  const cases = [
    // a correct key with a lying local_id would instruct the wrong Work
    [envelope([{ ...workAction("7ba67cb8-W5"), local_id: "W999" }]), /local_id "W999" disagrees/],
    [envelope([{ ...workAction("7ba67cb8-W5"), local_id: 5 }]), /local_id 5 disagrees/],
    // a string "false" is truthy: claimed must be an actual boolean
    [envelope([{ ...workAction("7ba67cb8-W5"), claimed: "false" }]), /claimed is not a boolean/],
    [envelope([{ ...workAction("7ba67cb8-W5"), title: 7 }]), /title is not a string/],
    [envelope([{ ...obligationAction(9, "7ba67cb8-W2"), flavor: 3 }]), /flavor is not a string/],
    [envelope([{ ...roundAction("7ba67cb8-W3", 1, 1), review_at: 0 }]), /review_at is not a string/],
    // structurally valid but impossible ids refuse
    [{ ...envelope([]), snapshot_seq: -1 }, /non-negative snapshot_seq/],
    [envelope([{ ...obligationAction(0, "7ba67cb8-W2"), action_key: "obligation:0" }]), /no positive seq/],
    [envelope([{ ...roundAction("7ba67cb8-W3", 0, 1), action_key: "round:7ba67cb8-W3:0:1" }]), /positive work\/round\/generation/],
    [envelope([{ ...roundAction("7ba67cb8-W3", 1, -2), action_key: "round:7ba67cb8-W3:1:-2" }]), /positive work\/round\/generation/],
  ];
  for (const [payload, pattern] of cases) {
    assert.throws(() => validateEnvelope(payload, "baton.codex"), pattern);
  }
  // optional descriptive fields stay optional when absent
  const bare = envelope([{ kind: "work", action_key: "work:7ba67cb8-W5", work: "7ba67cb8-W5" }]);
  assert.equal(validateEnvelope(bare, "baton.codex").snapshot_seq, 42);
});

test("the real invocation is the documented argv through the executor boundary", async () => {
  const invocations = [];
  const controller = new AbortController();
  const events = [];
  await codexBatonBridge(
    {
      baton: "/opt/baton/v11/bin/baton",
      config: "/home/user/baton-v11/baton.json",
      participant: "baton.codex",
      target: "baton",
      "wait-timeout": "45",
      once: true,
    },
    {
      signal: controller.signal,
      execute: async (file, argv) => {
        invocations.push({ file, argv });
        return { stdout: JSON.stringify(envelope([workAction("7ba67cb8-W5")])) };
      },
      emitEvent: async (_socket, event) => { events.push(event); return { accepted: true }; },
      logger: { info() {}, warn() {} },
    },
  );
  assert.equal(invocations.length, 1);
  assert.equal(invocations[0].file, "/opt/baton/v11/bin/baton");
  assert.deepEqual(invocations[0].argv, [
    "--config", "/home/user/baton-v11/baton.json",
    "--participant", "baton.codex",
    "wait", "timeout=45",
  ]);
  assert.equal(events.length, 1);
});
