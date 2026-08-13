import test from "node:test";
import assert from "node:assert/strict";
import { monitorBaton } from "../src/baton_source.mjs";

test("forwards message readiness without consuming Baton", async () => {
  const waits = [];
  const events = [];
  const code = await monitorBaton({ participant: "baton.reviewer", target: "baton", once: true }, {
    runWait: async () => {
      waits.push(true);
      return { ready: true, channel: "message", message_id: "abc123", damaged: false, from_participant: "baton.implementer" };
    },
    emitEvent: async (_socket, event) => {
      events.push(event);
      return { accepted: true };
    },
    logger: { info() {}, warn() {} },
  });
  assert.equal(code, 0);
  assert.equal(waits.length, 1);
  assert.equal(events[0].id, "baton:baton.reviewer:message:abc123");
  assert.equal(events[0].target, "baton");
  assert.match(events[0].summary, /abc123/);
});

test("forwards notice readiness as one batch event", async () => {
  const events = [];
  await monitorBaton({ participant: "baton.reviewer", target: "baton", once: true }, {
    runWait: async () => ({ ready: true, channel: "notice" }),
    emitEvent: async (_socket, event) => {
      events.push(event);
      return { accepted: true };
    },
    logger: { info() {}, warn() {} },
  });
  assert.equal(events[0].type, "notice-ready");
  assert.equal(events[0].id, "baton:baton.reviewer:notice-batch");
});
