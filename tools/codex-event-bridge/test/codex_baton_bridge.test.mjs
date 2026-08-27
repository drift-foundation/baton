// W148: focused Node coverage for the standalone v11 readiness
// producer — every acceptance case named in the finding, with the v10
// adapter suite untouched beside it.

import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { actionEvent, actionLocator, codexBatonBridge, validateEnvelope } from "../src/codex_baton_bridge.mjs";

const UUID = "7ba67cb8585dcfd250799fe0dc16e3fa";

function envelope(actions, { timedOut = false, participant = "baton.codex", uuid = UUID, projection = "7.0" } = {}) {
  return {
    protocol_version: 11,
    projection_version: projection,
    participant,
    authority_uuid: uuid,
    snapshot_seq: 42,
    result: { actionable: actions, timed_out: timedOut },
  };
}

// W49: the Work action key is an EPISODE locator — work id, assignment
// episode, accepted configuration generation — and must agree with the
// structured fields beside it.
function workAction(id, { claimed = false, title = "t", episode = 1, generation = 1 } = {}) {
  return { kind: "work", action_key: `work:${id}:${episode}:g${generation}`, work: id,
           episode_seq: episode, config_generation: generation,
           local_id: id.split("-").pop(), title, phase: "queued", claimed };
}

function obligationAction(seq, work) {
  return { kind: "obligation", action_key: `obligation:${seq}`, seq, work, flavor: "response" };
}

// W5 slice B: a poke is a CONSUMED kind now, so it gets a fixture like
// every other one. It deliberately carries no `work` — that absence is
// the primitive's whole point.
function pokeAction(seq, { asker = "baton.slaw", request = "what's up?",
                           expiresAt = null } = {}) {
  return { kind: "poke", action_key: `poke:${seq}`, poke: seq, asker,
           request, expires_at: expiresAt,
           asked_at: "2026-08-19T03:00:00Z" };
}

function trialAction(work, trial, generation) {
  return {
    kind: "due_trial",
    action_key: `trial:${work}:${trial}:${generation}`,
    work,
    trial,
    deadline_generation: generation,
    review_at: "2026-08-16T12:00:00Z",
  };
}

// W11910: an offer retry has a DEADLINE, so every run gets a clock it
// controls. Frozen unless a test advances it deliberately — otherwise
// whether a bounded retry fired would depend on the test's own wall
// time, which is not a property worth asserting.
function clock(start = 1_000_000) {
  let value = start;
  return { now: () => value, advance(ms) { value += ms; return value; } };
}

function harness(script, { now = clock().now, ...options } = {}) {
  const events = [];
  const controller = new AbortController();
  let calls = 0;
  const run = codexBatonBridge({ participant: "baton.codex", target: "baton", "retry-ms": "1", ...options }, {
    signal: controller.signal,
    now,
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
    logger: options.logger ?? { info() {}, warn() {} },
  });
  return { run, events, controller };
}

test("multiple simultaneous action keys each emit one scoped event", async () => {
  const actions = [
    obligationAction(9, "7ba67cb8-W2"),
    trialAction("7ba67cb8-W3", 1, 1),
    workAction("7ba67cb8-W5"),
  ];
  const { run, events } = harness([envelope(actions)]);
  await run;
  assert.equal(events.length, 3);
  assert.deepEqual(events.map((event) => event.id), [
    `baton-v11:${UUID}:baton.codex:obligation:9`,
    `baton-v11:${UUID}:baton.codex:trial:7ba67cb8-W3:1:1`,
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5:1:g1`,
  ]);
  for (const event of events) {
    assert.equal(event.source, "baton-v11");
    assert.equal(event.type, "v11-action-ready");
    assert.match(event.summary, /canonical v11 CLI/);
    assert.doesNotMatch(event.details, /body/);
  }
});

// -- W11910: readiness stays armed until the canonical claim -----------
//
// `work/records/2026/08/finding-readiness-offer-cleared-before-claim/`.
//
// This case used to be one test asserting that a persistent unclaimed
// key is suppressed after the socket accepts it. That conflated two
// different rules, and the wrong half of it was the live defect: an
// accepted event is TRANSPORT acknowledgement, and a managed turn that
// forwarded it may well have ended without claiming anything. The
// authority's `claimed:true` is the acknowledgement. So the case is
// split — an unclaimed offer stays armed and is retried under a bounded
// deadline; the claim, and only the claim, clears it.

test("an unclaimed offer is retained, not spent again, before its deadline", async () => {
  const set = [workAction("7ba67cb8-W5")];
  const { run, events } = harness([envelope(set), envelope(set), envelope(set)]);
  await run;
  assert.equal(events.length, 1, "an unclaimed offer busy-looped the target");
});

test("an unclaimed offer is forwarded again once its deadline passes", async () => {
  const time = clock();
  const set = [workAction("7ba67cb8-W5")];
  const { run, events } = harness([
    envelope(set),
    envelope(set),
    // the managed turn ended without claiming and canonical state is
    // unchanged, so the offer stands — and this process re-offers it
    // rather than needing to be restarted
    () => { time.advance(60_000); return envelope(set); },
  ], { now: time.now });
  await run;
  assert.equal(events.length, 2, "a turn that never claimed cleared the offer");
  assert.equal(events[0].id, events[1].id);
});

test("claiming the same Work acknowledges it rather than duplicating its wake", async () => {
  const time = clock();
  const { run, events } = harness([
    envelope([workAction("7ba67cb8-W5")]),
    // far past any retry deadline: it is the CLAIM that clears this
    () => { time.advance(600_000); return envelope([workAction("7ba67cb8-W5", { claimed: true })]); },
    () => { time.advance(600_000); return envelope([workAction("7ba67cb8-W5", { claimed: true })]); },
  ], { now: time.now });
  await run;
  assert.equal(events.length, 1, "the claim manufactured a second event");
});

test("a producer starting on a live claim still forwards one recovery wake", async () => {
  const claimed = [workAction("7ba67cb8-W2907", { claimed: true })];
  const { run, events } = harness([envelope(claimed), envelope(claimed)]);
  await run;
  assert.equal(events.length, 1, "claimed-Work restart recovery changed");
  assert.equal(events[0].action.claimed, true);
});

test("an unclaimed offer waits for the claim slot and is forwarded when it frees", async () => {
  const held = workAction("7ba67cb8-W6627", { claimed: true });
  const waiting = workAction("7ba67cb8-W10265");
  const { run, events } = harness([
    envelope([held, waiting]),
    envelope([held, waiting]),
    envelope([waiting]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.action.key),
                   [held.action_key, waiting.action_key],
                   "an occupied claim slot was given work it cannot take");
});

test("the producer admits one unclaimed Work per poll, in canonical order", async () => {
  // Review [P1] renamed this. It used to claim the head was held "until
  // its outcome is known", which this file cannot check: `markPresented`
  // runs here on socket ACCEPTANCE, before the dispatcher has started
  // the turn, so the producer never learns the outcome at all. What it
  // does assert is real and worth keeping — one per poll, canonical
  // order — and the claim-slot boundary it does NOT assert is proved
  // across the producer and the dispatcher in `test/claim_slot.test.mjs`.
  const first = workAction("7ba67cb8-W6630");
  const second = workAction("7ba67cb8-W6632");
  const { run, events } = harness([
    envelope([first, second]),
    envelope([first, second]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.action.key),
                   [first.action_key, second.action_key]);
});

test("obligations, trials and pokes beside a deferred Work keep their own rule", async () => {
  const held = workAction("7ba67cb8-W6627", { claimed: true });
  const waiting = workAction("7ba67cb8-W10265");
  const { run, events } = harness([
    envelope([held, waiting, obligationAction(9, "7ba67cb8-W2"),
              trialAction("7ba67cb8-W3", 1, 1), pokeAction(4)]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.action.key),
                   [held.action_key, "obligation:9", "trial:7ba67cb8-W3:1:1",
                    "poke:4"]);
});

test("a retained offer withdrawn while it waits is never forwarded", async () => {
  const held = workAction("7ba67cb8-W6627", { claimed: true });
  const waiting = workAction("7ba67cb8-W10265");
  const { run, events } = harness([
    envelope([held, waiting]),
    // blocked, rerouted, parked, superseded or closed
    envelope([held]),
    envelope([], { timedOut: true }),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.action.key), [held.action_key]);
});

test("a dispatcher already holding the delivery keeps the offer armed", async () => {
  // The dispatcher retains the exact v11 event id for the whole
  // queued/starting/ambiguous/active lifetime, so a bounded retry of an
  // unclaimed offer is refused as `in-flight`. That is neither a failure
  // to report nor an acknowledgement: the offer backs off and stands.
  const time = clock();
  const set = [workAction("7ba67cb8-W5")];
  const warnings = [];
  let forwarded = 0;
  const { run, events } = harness([
    envelope(set),
    () => { time.advance(60_000); return envelope(set); },
    () => { time.advance(60_000); return envelope(set); },
    () => { time.advance(60_000); return envelope([workAction("7ba67cb8-W5", { claimed: true })]); },
  ], { now: time.now,
       respond: (event) => {
         forwarded += 1;
         // the first delivery is queued; every retry meets the retained
         // identity of a delivery this dispatcher is still holding
         return forwarded === 1
           ? { accepted: true, reason: "queued", eventId: event.id }
           : { accepted: false, reason: "in-flight", eventId: event.id };
       },
       logger: { info() {}, warn(message) { warnings.push(message); } } });
  await run;
  assert.equal(events.length, 3,
    "an in-flight refusal cleared the offer instead of keeping it armed");
  assert.deepEqual(warnings, [], "an in-flight refusal was reported as a failure");
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
    envelope([obligationAction(9, "7ba67cb8-W2"), trialAction("7ba67cb8-W3", 1, 1)]),
    envelope([obligationAction(12, "7ba67cb8-W2"), trialAction("7ba67cb8-W3", 1, 2)]),
  ]);
  await run;
  assert.deepEqual(events.map((event) => event.id.split(":").slice(2).join(":")), [
    "baton.codex:obligation:9",
    "baton.codex:trial:7ba67cb8-W3:1:1",
    "baton.codex:obligation:12",
    "baton.codex:trial:7ba67cb8-W3:1:2",
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
    envelope([{ kind: "work", action_key: "work:x:1:g1" }]),
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
  const trial = actionLocator(trialAction("7ba67cb8-W3", 2, 5));
  assert.deepEqual(trial, {
    kind: "due_trial",
    action_key: "trial:7ba67cb8-W3:2:5",
    work: "7ba67cb8-W3",
    trial: 2,
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
  assert.equal(event.id, `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5:1:g1`);
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
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5:1:g1`,
    `baton-v11:${OTHER}:baton.codex:work:7ba67cb8-W5:1:g1`,
    `baton-v11:${UUID}:baton.codex:work:7ba67cb8-W5:1:g1`,
  ]);
});

test("the typed contract refuses every inconsistent envelope by name", () => {
  const cases = [
    // incompatible projection (W207): pre-contract majors and missing
    [envelope([], { projection: "4.3" }), /projection-7\/8\/9\/10\/11\/12 participant-action contract/],
    [envelope([], { projection: "4.5" }), /projection-7\/8\/9\/10\/11\/12 participant-action contract/],
    [envelope([], { projection: "5.0" }), /projection-7\/8\/9\/10\/11\/12 participant-action contract/],
    [envelope([], { projection: "6.9" }), /projection-7\/8\/9\/10\/11\/12 participant-action contract/],
    [{ ...envelope([]), projection_version: undefined }, /projection-7\/8\/9\/10\/11\/12 participant-action contract/],
    // missing snapshot token / non-boolean timed_out
    [{ ...envelope([]), snapshot_seq: "42" }, /snapshot_seq/],
    [{ ...envelope([]), result: { actionable: [], timed_out: "no" } }, /timed_out is not a boolean/],
    // contradictory timeout: timed out yet carrying actions
    [envelope([workAction("7ba67cb8-W5")], { timedOut: true }), /contradictory/],
    // an unknown KIND is no longer here: W5's ruled disposition makes it
    // tolerated (see the tolerance test below). What stays refused is
    // envelope STRUCTURE, which every entry owes whatever its kind:
    [envelope([{ kind: "message" }]), /no stable action_key/],
    [envelope([{ kind: "message", action_key: "" }]), /no stable action_key/],
    // malformed per-kind payloads
    [envelope([{ kind: "work", action_key: "work:7ba67cb8-W5:1:g1" }]), /names no Work/],
    [envelope([{ kind: "obligation", action_key: "obligation:9", work: "7ba67cb8-W2" }]), /has no positive seq/],
    [envelope([{ kind: "due_trial", action_key: "trial:7ba67cb8-W3:1:1", work: "7ba67cb8-W3", trial: 1 }]), /lacks its positive work\/trial\/generation locator/],
    // W5 slice B: consumed means TYPED. Tolerance is for kinds this
    // build does not know, never for one it does.
    [envelope([{ kind: "poke", action_key: "poke:7" }]), /no positive poke sequence/],
    [envelope([{ ...pokeAction(7), action_key: "poke:9" }]), /disagrees with poke 7/],
    [envelope([{ ...pokeAction(7), asker: "" }]), /names no asker/],
    [envelope([{ ...pokeAction(7), request: "" }]), /carries no request text/],
    [envelope([{ ...pokeAction(7), expires_at: 3 }]), /expires_at is not a string/],
    [envelope([{ ...pokeAction(7), work: "7ba67cb8-W2" }]), /a poke belongs to none/],
    // key/field disagreement, one per kind
    [envelope([{ ...workAction("7ba67cb8-W5"), action_key: "work:7ba67cb8-W9:1:g1" }]), /disagrees with work/],
    [envelope([{ ...obligationAction(9, "7ba67cb8-W2"), action_key: "obligation:12" }]), /disagrees with seq/],
    [envelope([{ ...trialAction("7ba67cb8-W3", 1, 1), action_key: "trial:7ba67cb8-W3:1:2" }]), /disagrees with its locator/],
    // duplicate action key
    [envelope([workAction("7ba67cb8-W5"), workAction("7ba67cb8-W5")]), /duplicate action_key/],
  ];
  for (const [payload, pattern] of cases) {
    assert.throws(() => validateEnvelope(payload, "baton.codex"), pattern);
  }
  // and the boundary the gate is FOR: a later 7.x minor stays accepted
  assert.equal(validateEnvelope(envelope([], { projection: "7.4" }), "baton.codex").snapshot_seq, 42);
  // Projection 8 changed claimant-authority semantics without changing this
  // fully typed participant-action envelope. The transition bridge accepts
  // both bounded majors, never arbitrary future ones.
  assert.equal(validateEnvelope(envelope([], { projection: "8.0" }), "baton.codex").snapshot_seq, 42);
  // W38/W78: projection 9 changed the phase value set and projection 10
  // changed detail presentation, but the participant-action envelope's own
  // fields did not, so the bounded transition window is 7/8/9/10.
  assert.equal(validateEnvelope(envelope([], { projection: "9.0" }), "baton.codex").snapshot_seq, 42);
  assert.equal(validateEnvelope(envelope([], { projection: "10.0" }), "baton.codex").snapshot_seq, 42);
  // W155: projection 11 is now SUPPORTED — the tree window's third
  // level added a value to the consumed `depth` domain, so the major
  // moved and this consumer moved with it. 12 is the unsupported future.
  assert.equal(validateEnvelope(envelope([], { projection: "11.0" }), "baton.codex").projection_version, "11.0");
  // W5: projection 12 carries the `poke` action kind. A consumer built
  // before the tolerance widening REFUSES an envelope containing it —
  // the whole envelope — which is the documented major-version
  // condition, so the major moved and this consumer moved with it.
  assert.equal(validateEnvelope(envelope([], { projection: "12.0" }), "baton.codex").projection_version, "12.0");
  assert.throws(() => validateEnvelope(envelope([], { projection: "13.0" }), "baton.codex"), /projection-7\/8\/9\/10\/11\/12 participant-action contract/);
});

test("a poke is forwarded with the question and how to answer it", () => {
  // W5 slice B: the compact event a Codex target receives. The summary
  // is the friendly question; the locator carries exactly what
  // `poke-answer` needs, so the agent does not re-read the projection
  // to find a sequence it was already told.
  const action = pokeAction(7, { asker: "baton.slaw",
                                 request: "still on W12?" });
  const event = actionEvent(envelope([action]), action,
                            { target: "baton-reviewer" });
  assert.equal(event.id,
               `baton-v11:${UUID}:baton.codex:poke:7`);
  assert.match(event.summary, /baton\.slaw asks baton\.codex: still on W12\?/);
  assert.match(event.summary, /poke-answer poke=7/);
  assert.doesNotMatch(event.summary, /alert|alarm|escalat|unhealthy/i);
  const locator = JSON.parse(event.details);
  assert.deepEqual(locator, {
    kind: "poke", action_key: "poke:7", poke: 7, asker: "baton.slaw",
    request: "still on W12?", expires_at: null,
  });
  // a poke names no Work, and the locator must not invent one
  assert.equal(locator.work, undefined);
});


test("an unknown action kind is ignored and the rest of the envelope survives", () => {
  // W5 (finding-conversational-agent-poke), ruled 2026-08-18: an action
  // kind this build does not know is ignored with a diagnostic, and the
  // rest of the envelope is retained. Before this the final `else` threw,
  // so ONE unreadable entry rejected the whole wait result and the agent
  // stopped receiving its ordinary Work and obligation wakes as well —
  // an outage, not a missed feature. That is the assertion this replaces.
  const work = workAction("7ba67cb8-W5");
  const obligation = obligationAction(9, "7ba67cb8-W2");
  // W5 slice B made `poke` a KNOWN kind, so this now uses a kind that
  // is genuinely unreadable — which is what the test always meant. The
  // point is the entry BESIDE the unreadable one, not which word is
  // unreadable this week.
  const payload = envelope([
    obligation,
    { kind: "some_future_kind", action_key: "future:7" },
    work,
  ]);
  const validated = validateEnvelope(payload, "baton.codex");

  // the KNOWN entries survive, in order, unchanged
  assert.deepEqual(validated.result.actionable.map((a) => a.action_key),
                   [obligation.action_key, work.action_key]);
  // and the skew is reported rather than silently swallowed
  assert.deepEqual(validated.result.ignored_actions,
                   [{ kind: "some_future_kind", action_key: "future:7" }]);

  // an envelope of NOTHING BUT unknown entries is still a valid empty
  // wait result, not a refusal
  const only = validateEnvelope(
    envelope([{ kind: "some_future_kind", action_key: "future:8" }]),
    "baton.codex");
  assert.deepEqual(only.result.actionable, []);
  assert.deepEqual(only.result.ignored_actions,
                   [{ kind: "some_future_kind", action_key: "future:8" }]);

  // tolerance is for the KIND alone: a known kind stays as strictly
  // typed as it ever was, and duplicate keys still refuse across kinds
  assert.throws(() => validateEnvelope(
    envelope([{ kind: "work", action_key: "work:7ba67cb8-W5:1:g1" }]),
    "baton.codex"), /names no Work/);
  assert.throws(() => validateEnvelope(
    envelope([{ kind: "some_future_kind", action_key: "future:7" },
              { kind: "other_future_kind", action_key: "future:7" }]),
    "baton.codex"), /duplicate action_key/);

  // a well-formed envelope gains an EMPTY ignored list, so a caller can
  // read it unconditionally
  assert.deepEqual(
    validateEnvelope(envelope([work]), "baton.codex").result.ignored_actions,
    []);
});

test("the bridge accepts the repository's current projection", () => {
  const source = readFileSync(new URL("../../../src/baton_work/jsonapi.py", import.meta.url), "utf8");
  const match = /^PROJECTION_VERSION = "([^"]+)"$/m.exec(source);
  assert.ok(match, "baton_work.jsonapi names no projection version");
  assert.equal(validateEnvelope(envelope([], { projection: match[1] }), "baton.codex").projection_version, match[1]);
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
    [envelope([{ ...trialAction("7ba67cb8-W3", 1, 1), review_at: 0 }]), /review_at is not a string/],
    // structurally valid but impossible ids refuse
    [{ ...envelope([]), snapshot_seq: -1 }, /non-negative snapshot_seq/],
    [envelope([{ ...obligationAction(0, "7ba67cb8-W2"), action_key: "obligation:0" }]), /no positive seq/],
    [envelope([{ ...trialAction("7ba67cb8-W3", 0, 1), action_key: "trial:7ba67cb8-W3:0:1" }]), /positive work\/trial\/generation/],
    [envelope([{ ...trialAction("7ba67cb8-W3", 1, -2), action_key: "trial:7ba67cb8-W3:1:-2" }]), /positive work\/trial\/generation/],
  ];
  for (const [payload, pattern] of cases) {
    assert.throws(() => validateEnvelope(payload, "baton.codex"), pattern);
  }
  // optional DESCRIPTIVE fields stay optional when absent. W49 moved
  // episode_seq and config_generation out of that set: they are the
  // action's identity, not description, so a bare action still carries
  // them and the key still has to agree.
  //
  // W11910 R5 moved `claimed` out of it too, with the review's explicit
  // case-specific confirmation to revise this assertion. The rule the set is
  // drawn on has not changed — a field this build SCHEDULES on is not
  // descriptive — and `claimed` became a scheduling input when the claim slot
  // started deciding whether a Work may take a turn. `local_id`, `title` and
  // `phase` describe the Work and nothing reads them to decide anything, so
  // they stay optional and the bare action below still proves it.
  const bare = envelope([{ kind: "work", action_key: "work:7ba67cb8-W5:1:g1",
                           work: "7ba67cb8-W5", episode_seq: 1,
                           config_generation: 1, claimed: false }]);
  assert.equal(validateEnvelope(bare, "baton.codex").snapshot_seq, 42);
  // And the field is REQUIRED rather than merely typed, which is the half the
  // fifth review found missing: absence read as `claimed === true` being
  // false is a Work answering "nobody holds the slot" about a slot it may
  // itself hold.
  const { claimed, ...unread } = bare.result.actionable[0];
  assert.throws(
    () => validateEnvelope(envelope([unread]), "baton.codex"),
    /carries no claimed verdict/);
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

// -- W93 R21: the refresh reaches the dispatcher, never a model -------------

function refreshAction(generation = 7, { incarnation = "run-1",
                                        at = "2026-08-19T11:00:00Z" } = {}) {
  // R25: the key is built from the GENERATION, never the instant.
  return { kind: "runtime_refresh",
           action_key: `runtime-refresh:${incarnation}:${generation}`,
           incarnation, generation, requested_at: at, wakes_model: false };
}

test("a refresh is handed to the dispatcher as a control, not an event", async () => {
  // The producer is the ONLY consumer that sees the request, and it
  // does not own the lease. Dropping it here — the round-1 behaviour —
  // removed the signal at the one place it arrived.
  const { run, events } = harness([envelope([refreshAction()])]);
  await run;
  assert.equal(events.length, 1);
  const [message] = events;
  assert.equal(message.control, "runtime-refresh");
  assert.equal(message.target, "baton");
  assert.equal(message.participant, "baton.codex");
  assert.equal(message.incarnation, "run-1");
  assert.equal(message.generation, 7);
  assert.equal(message.requested_at, "2026-08-19T11:00:00Z");
  // Not an event: nothing here can become a queued message or a turn.
  assert.equal(message.type, undefined);
  assert.equal(message.summary, undefined);
  assert.equal(message.source, undefined);
});

test("a refresh rides beside a real wake without displacing it", async () => {
  const { run, events } = harness([
    envelope([refreshAction(), workAction("7ba67cb8-W5")])]);
  await run;
  assert.deepEqual(events.map((entry) => entry.control ?? entry.type),
    ["runtime-refresh", "v11-action-ready"]);
});

test("--once waits for a wake to forward, and a refresh is not one", async () => {
  // Answering a diagnostic must not satisfy a run that exists to
  // deliver one action: the producer would exit having woken nobody.
  const { run, events } = harness(
    [envelope([refreshAction()]), envelope([refreshAction(), workAction("7ba67cb8-W5")])],
    { once: true });
  await run;
  assert.deepEqual(events.map((entry) => entry.control ?? entry.type),
    ["runtime-refresh", "v11-action-ready"]);
});

test("a refresh the dispatcher could not answer is retried", async () => {
  // The publication failed, so the request still stands. Retiring the
  // key would spend the one retry the level-triggered signal gives us.
  const asked = refreshAction(7);
  let attempts = 0;
  const { run, events } = harness([envelope([asked]), envelope([asked])], {
    respond: (message) => {
      if (message.control !== "runtime-refresh") return { accepted: true };
      attempts += 1;
      return attempts === 1
        ? { accepted: false, reason: "runtime-refresh-failed" }
        : { accepted: true, reason: "runtime-refresh" };
    },
  });
  await run;
  assert.equal(events.length, 2, "a failed refresh was not retried");
  assert.equal(attempts, 2);
});

test("an answered refresh is not asked again while the same key stands", async () => {
  const asked = refreshAction(7);
  const { run, events } = harness([envelope([asked]), envelope([asked])]);
  await run;
  assert.equal(events.length, 1);
});

test("two asks inside ONE second are two requests, not one", async () => {
  // R25: whole-second instants cannot identify ordered requests. Keyed
  // on the timestamp, the second ask was suppressed as a delivered
  // duplicate and the operator waited forever for an answer to it.
  const { run, events } = harness([
    envelope([refreshAction(7)]),
    envelope([refreshAction(8)])]);
  await run;
  assert.deepEqual(events.map((entry) => entry.generation), [7, 8]);
  assert.deepEqual(new Set(events.map((entry) => entry.requested_at)),
    new Set(["2026-08-19T11:00:00Z"]), "the clock did not move");
});

test("an entry with no generation cannot be answered exactly", async () => {
  const { generation, ...ungenerated } = refreshAction(7);
  assert.throws(() => validateEnvelope(envelope([ungenerated]), "baton.codex"),
    /no positive generation/);
});
