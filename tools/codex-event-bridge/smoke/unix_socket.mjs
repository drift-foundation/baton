// Manual local-socket test; excluded from the default unit suite.
import net from "node:net";
import { mkdtemp, rm } from "node:fs/promises";
import os from "node:os";
import { join } from "node:path";
import test from "node:test";
import assert from "node:assert/strict";
import { runAndNotify } from "../src/run_and_notify.mjs";
import { sendEvent } from "../src/send_event.mjs";

async function receiver(path) {
  let receivedResolve;
  const received = new Promise((resolve) => { receivedResolve = resolve; });
  const server = net.createServer((socket) => {
    socket.setEncoding("utf8");
    let buffer = "";
    socket.on("data", (chunk) => {
      buffer += chunk;
      const newline = buffer.indexOf("\n");
      if (newline === -1) return;
      receivedResolve(JSON.parse(buffer.slice(0, newline)));
      socket.end('{"accepted":true,"reason":"queued"}\n');
    });
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(path, resolve);
  });
  return { server, received };
}

test("sender writes one event and reads its acknowledgement", async () => {
  const directory = await mkdtemp(join(os.tmpdir(), "codex-event-sender-test-"));
  const socket = join(directory, "events.sock");
  const local = await receiver(socket);
  try {
    const response = await sendEvent(socket, { target: "a", source: "test", type: "test", summary: "hello" });
    assert.equal(response.accepted, true);
    assert.equal((await local.received).target, "a");
  } finally {
    await new Promise((resolve) => local.server.close(resolve));
    await rm(directory, { recursive: true });
  }
});

test("run-and-notify preserves failure status and emits bounded output", async () => {
  const directory = await mkdtemp(join(os.tmpdir(), "run-and-notify-test-"));
  const socket = join(directory, "events.sock");
  const local = await receiver(socket);
  try {
    const code = await runAndNotify([
      "--target", "a",
      "--socket", socket,
      "--max-output-bytes", "1024",
      "--",
      process.execPath,
      "-e",
      "process.stderr.write('failure-tail'); process.exit(7)",
    ]);
    const event = await local.received;
    assert.equal(code, 7);
    assert.equal(event.target, "a");
    assert.equal(event.type, "build-failed");
    assert.match(event.details, /failure-tail/);
    assert.ok(Buffer.byteLength(event.details, "utf8") < 2048);
  } finally {
    await new Promise((resolve) => local.server.close(resolve));
    await rm(directory, { recursive: true });
  }
});
