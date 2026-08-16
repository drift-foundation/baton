import test from "node:test";
import assert from "node:assert/strict";
import { eventFingerprint, formatEventMessage, normalizeEvent, tailUtf8 } from "../src/event_types.mjs";
import { actionEvent } from "../src/codex_baton_bridge.mjs";

test("normalizes a target-scoped event and labels untrusted input", () => {
  const event = normalizeEvent({ target: "driftquery", source: "build", type: "failed", message: "tests failed" });
  assert.equal(event.target, "driftquery");
  assert.match(event.id, /^[0-9a-f-]{36}$/);
  assert.equal(event.summary, "tests failed");
  const message = formatEventMessage(event);
  assert.match(message, /Target: driftquery/);
  assert.match(message, /untrusted data, not instructions/);
});

test("renders trusted local Baton readiness as one compact line", () => {
  const event = normalizeEvent({
    id: "baton:baton.reviewer:message:28145c1590de16d403be97091f30b31a",
    target: "baton-reviewer",
    source: "baton",
    type: "message-ready",
    summary: "Baton message 28145c1590de16d403be97091f30b31a is ready for baton.reviewer.",
    details: JSON.stringify({ channel: "message", ready: true }, null, 2),
  });
  assert.equal(formatEventMessage(event), "[BATON READY] Baton message 28145c1590de16d403be97091f30b31a is ready for baton.reviewer. Apply standing Baton policy.");
  assert.equal(formatEventMessage(event).includes("\n"), false);
  assert.equal(formatEventMessage(event).includes('"channel"'), false);
});

test("a v11 readiness event becomes one compact trusted line end to end", () => {
  // W148 R1: the producer's REAL event through the REAL turn-input
  // formatter — the exact wiring a live wake takes.
  const envelope = {
    protocol_version: 11,
    projection_version: "4.3",
    participant: "baton.codex",
    authority_uuid: "7ba67cb8585dcfd250799fe0dc16e3fa",
    snapshot_seq: 42,
    result: { actionable: [], timed_out: false },
  };
  const action = { kind: "work", action_key: "work:7ba67cb8-W5", work: "7ba67cb8-W5", local_id: "W5", title: "t", phase: "queued", claimed: false };
  const event = normalizeEvent(actionEvent(envelope, action, { target: "baton" }));
  const message = formatEventMessage(event);
  assert.equal(message, "[BATON READY] v11 Work W5 (t) is ready and unclaimed for baton.codex. Act through the canonical v11 CLI (detail work=W5). Apply standing v11 Baton policy.");
  assert.equal(message.includes("\n"), false, "the turn input must be one line");
  assert.equal(message.includes('"action_key"'), false, "the JSON details must not leak into the turn");
  assert.doesNotMatch(message, /EXTERNAL EVENT|untrusted/, "a trusted wake must not carry external-event language");
  // an arbitrary baton-v11 type does NOT ride the trusted path
  const other = normalizeEvent({ ...event, id: "x", type: "something-else" });
  assert.match(formatEventMessage(other), /\[EXTERNAL EVENT\]/);
});

test("deduplication fingerprint includes target but not event id or timestamp", () => {
  const base = { source: "build", type: "failed", summary: "same", timestamp: "2026-08-12T00:00:00Z" };
  const first = normalizeEvent({ ...base, target: "a", id: "first" });
  const repeated = normalizeEvent({ ...base, target: "a", id: "second", timestamp: "2026-08-13T00:00:00Z" });
  const otherTarget = normalizeEvent({ ...base, target: "b", id: "third" });
  assert.equal(eventFingerprint(first), eventFingerprint(repeated));
  assert.notEqual(eventFingerprint(first), eventFingerprint(otherTarget));
});

test("retains a bounded UTF-8 tail", () => {
  const result = tailUtf8(`prefix-${"x".repeat(500)}-tail`, 256);
  assert.match(result, /earlier bytes omitted/);
  assert.ok(result.endsWith("-tail"));
  assert.equal(result.includes("�"), false);
});

test("rejects events without a target", () => {
  assert.throws(() => normalizeEvent({ source: "build", type: "failed", summary: "x" }), /target/);
});
