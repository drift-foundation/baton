import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { defaultEventSocketPath } from "./config.mjs";
import { sendEvent } from "./send_event.mjs";

const execFileAsync = promisify(execFile);

function usage() {
  return `usage: baton-codex-monitor --baton PATH --config PATH --participant ADDRESS --target NAME [options]

options:
  --socket PATH       event bridge Unix socket
  --wait-timeout SEC  Baton wait timeout (default: 60)
  --retry-ms MS       delay after repeated readiness/errors (default: 1000)
  --once              exit after one event is accepted

This monitor is read-only. It never claims messages or sees notices.`;
}

function parse(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--once" || arg === "--help" || arg === "-h") {
      options[arg.replace(/^-+/, "")] = true;
      continue;
    }
    if (!arg.startsWith("--")) throw new Error(`unexpected argument: ${arg}`);
    const value = argv[++index];
    if (value === undefined) throw new Error(`${arg} requires a value`);
    options[arg.slice(2)] = value;
  }
  return options;
}

function positiveInteger(value, fallback, name) {
  const selected = value === undefined ? fallback : Number(value);
  if (!Number.isSafeInteger(selected) || selected < 1) throw new Error(`${name} must be a positive integer`);
  return selected;
}

function eventForReady(ready, options) {
  if (ready.channel === "message") {
    if (typeof ready.message_id !== "string" || !ready.message_id) throw new Error("Baton message readiness has no message_id");
    return {
      id: `baton:${options.participant}:message:${ready.message_id}`,
      target: options.target,
      source: "baton",
      type: ready.damaged ? "damaged-message-ready" : "message-ready",
      summary: `Baton message ${ready.message_id} is ready for ${options.participant}${ready.damaged ? " and is marked damaged" : ""}.`,
      details: JSON.stringify(ready, null, 2),
    };
  }
  if (ready.channel === "notice") {
    return {
      id: `baton:${options.participant}:notice-batch`,
      target: options.target,
      source: "baton",
      type: "notice-ready",
      summary: `One or more Baton notices are ready for ${options.participant}.`,
      details: JSON.stringify(ready, null, 2),
    };
  }
  throw new Error(`unsupported Baton readiness channel: ${ready.channel}`);
}

function delay(ms, signal) {
  if (signal.aborted) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(done, ms);
    signal.addEventListener("abort", done, { once: true });
    function done() {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolve();
    }
  });
}

export async function monitorBaton(options, { signal = new AbortController().signal, runWait, emitEvent = sendEvent, logger = console } = {}) {
  const waitTimeout = positiveInteger(options["wait-timeout"], 60, "--wait-timeout");
  const retryMs = positiveInteger(options["retry-ms"], 1000, "--retry-ms");
  const socket = options.socket ?? process.env.CODEX_EVENT_SOCKET ?? defaultEventSocketPath();
  let deliveredKey = null;
  while (!signal.aborted) {
    let ready;
    try {
      if (runWait) {
        ready = await runWait();
      } else {
        const result = await execFileAsync(options.baton, ["--config", options.config, "wait", "--participant", options.participant, "--timeout", String(waitTimeout)], {
          encoding: "utf8",
          maxBuffer: 1024 * 1024,
          signal,
        });
        ready = JSON.parse(result.stdout);
      }
    } catch (error) {
      if (signal.aborted || error.name === "AbortError") break;
      if (error.code === 3) {
        deliveredKey = null;
        continue;
      }
      logger.warn(`Baton wait failed: ${error.message}; retrying in ${retryMs}ms`);
      await delay(retryMs, signal);
      continue;
    }
    if (!ready?.ready) {
      deliveredKey = null;
      continue;
    }
    const event = eventForReady(ready, options);
    if (event.id === deliveredKey) {
      await delay(retryMs, signal);
      continue;
    }
    try {
      const response = await emitEvent(socket, event);
      if (!response.accepted && response.reason !== "duplicate") {
        throw new Error(`event rejected: ${JSON.stringify(response)}`);
      }
      deliveredKey = event.id;
      logger.info(`Baton readiness forwarded: ${ready.channel}${ready.message_id ? ` ${ready.message_id}` : ""} -> ${options.target}`);
      if (options.once) return 0;
    } catch (error) {
      logger.warn(`could not forward Baton readiness: ${error.message}; retrying in ${retryMs}ms`);
      await delay(retryMs, signal);
    }
  }
  return 0;
}

export async function runBatonMonitor(argv = process.argv.slice(2)) {
  const options = parse(argv);
  if (options.help || options.h) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  for (const name of ["baton", "config", "participant", "target"]) {
    if (!options[name]) throw new Error(`--${name} is required`);
  }
  const controller = new AbortController();
  process.once("SIGINT", () => controller.abort());
  process.once("SIGTERM", () => controller.abort());
  return await monitorBaton(options, { signal: controller.signal });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runBatonMonitor().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`baton-codex-monitor: ${error.message}\n`);
    process.exitCode = 2;
  });
}
