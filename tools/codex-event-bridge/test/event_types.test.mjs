import test from "node:test";
import assert from "node:assert/strict";
import { eventFingerprint, formatEventMessage, normalizeEvent, tailUtf8 } from "../src/event_types.mjs";

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
