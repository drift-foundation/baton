import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { join, resolve } from "node:path";
import { loadConfig } from "./config.mjs";
import { sendEvent } from "./send_event.mjs";

const toolRoot = fileURLToPath(new URL("..", import.meta.url));

function usage() {
  return `usage: codex-baton-stack --config PATH [--debug]

Starts every configured loopback Codex app-server, one shared event bridge,
and one read-only Baton readiness monitor per configured target.`;
}

function parse(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--debug" || arg === "--help" || arg === "-h") {
      options[arg.replace(/^-+/, "")] = true;
      continue;
    }
    if (arg !== "--config") throw new Error(`unexpected argument: ${arg}`);
    const value = argv[++index];
    if (value === undefined) throw new Error("--config requires a value");
    options.config = value;
  }
  return options;
}

export function buildStackPlan(config) {
  if (!config.baton) throw new Error("stack config requires baton.binary and baton.config");
  const monitors = [];
  for (const [target, value] of Object.entries(config.targets)) {
    if (!value.participant) throw new Error(`target ${target} requires participant for the all-session stack`);
    monitors.push(Object.freeze({ target, participant: value.participant }));
  }
  return Object.freeze({
    servers: Object.freeze(Object.entries(config.servers).map(([name, value]) => Object.freeze({ name, endpoint: value.endpoint }))),
    monitors: Object.freeze(monitors),
    baton: config.baton,
    eventSocket: config.eventSocket,
    startupTimeoutMs: config.startupTimeoutMs,
  });
}

function readyUrl(endpoint) {
  const url = new URL(endpoint);
  url.protocol = "http:";
  url.pathname = "/readyz";
  return url.href;
}

function delay(ms, signal) {
  if (signal.aborted) return Promise.resolve();
  return new Promise((resolveDelay) => {
    const timer = setTimeout(done, ms);
    signal.addEventListener("abort", done, { once: true });
    function done() {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolveDelay();
    }
  });
}

async function waitForHttp(endpoint, timeoutMs, signal) {
  const deadline = Date.now() + timeoutMs;
  let lastError = null;
  while (!signal.aborted && Date.now() < deadline) {
    try {
      const response = await fetch(readyUrl(endpoint), { signal });
      if (response.ok) return;
      lastError = new Error(`HTTP ${response.status}`);
    } catch (error) {
      if (signal.aborted) throw new Error("stack startup interrupted");
      lastError = error;
    }
    await delay(100, signal);
  }
  throw new Error(`app-server at ${endpoint} did not become ready within ${timeoutMs}ms${lastError ? `: ${lastError.message}` : ""}`);
}

async function waitForBridge(path, timeoutMs, signal) {
  const deadline = Date.now() + timeoutMs;
  let lastStatus = null;
  while (!signal.aborted && Date.now() < deadline) {
    try {
      lastStatus = await sendEvent(path, { control: "status" }, { timeoutMs: 500 });
      if (lastStatus.ready) return;
    } catch {}
    await delay(100, signal);
  }
  const unavailable = Object.entries(lastStatus?.targets ?? {}).filter(([, status]) => !status.loaded).map(([name]) => name);
  const detail = unavailable.length > 0 ? `; unavailable targets: ${unavailable.join(", ")}` : "";
  throw new Error(`event bridge did not load every target within ${timeoutMs}ms${detail}`);
}

function waitForExit(child, timeoutMs) {
  if (child.exitCode !== null || child.signalCode !== null) return Promise.resolve(true);
  return new Promise((resolveExit) => {
    const timer = setTimeout(() => done(false), timeoutMs);
    const exited = () => done(true);
    child.once("exit", exited);
    function done(result) {
      clearTimeout(timer);
      child.off("exit", exited);
      resolveExit(result);
    }
  });
}

export async function runStack(argv = process.argv.slice(2)) {
  const options = parse(argv);
  if (options.help || options.h) {
    process.stdout.write(`${usage()}\n`);
    return 0;
  }
  if (!options.config) throw new Error("--config is required");
  const configPath = resolve(options.config);
  const config = await loadConfig(configPath);
  const plan = buildStackPlan(config);
  const controller = new AbortController();
  const children = [];
  let stopping = false;
  let resolveUnexpected;
  const unexpectedExit = new Promise((resolveExit) => { resolveUnexpected = resolveExit; });

  const spawnChild = (label, command, args) => {
    const child = spawn(command, args, { stdio: "inherit" });
    const entry = { label, child };
    children.push(entry);
    child.once("error", (error) => {
      if (!stopping) resolveUnexpected(new Error(`${label} failed to start: ${error.message}`));
    });
    child.once("exit", (code, signal) => {
      if (!stopping) resolveUnexpected(new Error(`${label} exited unexpectedly (${signal ? `signal ${signal}` : `status ${code}`})`));
    });
    return child;
  };

  const requestedStop = new Promise((resolveStop) => {
    const stop = (signal) => {
      if (stopping) return;
      stopping = true;
      controller.abort();
      process.stderr.write(`codex-baton-stack: received ${signal}; stopping\n`);
      resolveStop({ requested: true });
    };
    process.once("SIGINT", () => stop("SIGINT"));
    process.once("SIGTERM", () => stop("SIGTERM"));
  });

  let failure = null;
  try {
    for (const server of plan.servers) {
      process.stderr.write(`codex-baton-stack: starting app-server ${server.name} at ${server.endpoint}\n`);
      spawnChild(`app-server ${server.name}`, "codex", ["app-server", "--listen", server.endpoint]);
    }
    await Promise.race([
      Promise.all(plan.servers.map((server) => waitForHttp(server.endpoint, plan.startupTimeoutMs, controller.signal))),
      unexpectedExit.then((error) => { throw error; }),
    ]);

    const bridgeArgs = [join(toolRoot, "src", "main.mjs"), "--config", configPath];
    if (options.debug) bridgeArgs.push("--debug");
    process.stderr.write(`codex-baton-stack: starting bridge for ${plan.monitors.length} targets\n`);
    spawnChild("event bridge", process.execPath, bridgeArgs);
    await Promise.race([
      waitForBridge(plan.eventSocket, plan.startupTimeoutMs, controller.signal),
      unexpectedExit.then((error) => { throw error; }),
    ]);

    for (const monitor of plan.monitors) {
      process.stderr.write(`codex-baton-stack: wiring ${monitor.participant} -> ${monitor.target}\n`);
      spawnChild(`Baton monitor ${monitor.participant}`, process.execPath, [
        join(toolRoot, "src", "baton_source.mjs"),
        "--baton", plan.baton.binary,
        "--config", plan.baton.config,
        "--participant", monitor.participant,
        "--target", monitor.target,
        "--socket", plan.eventSocket,
        "--wait-timeout", String(plan.baton.waitTimeoutSeconds),
        "--retry-ms", String(plan.baton.retryMs),
      ]);
    }
    process.stderr.write(`codex-baton-stack: ready; attach TUIs with ${plan.servers.map((server) => `codex --remote ${server.endpoint}`).join(" or ")}\n`);
    const outcome = await Promise.race([unexpectedExit.then((error) => ({ error })), requestedStop]);
    if (outcome.error) throw outcome.error;
  } catch (error) {
    failure = error;
  } finally {
    stopping = true;
    controller.abort();
    for (const { child } of [...children].reverse()) {
      if (child.exitCode === null && child.signalCode === null) child.kill("SIGTERM");
    }
    for (const { label, child } of [...children].reverse()) {
      if (!await waitForExit(child, 5000)) {
        process.stderr.write(`codex-baton-stack: ${label} did not stop after SIGTERM; sending SIGKILL\n`);
        child.kill("SIGKILL");
        await waitForExit(child, 1000);
      }
    }
  }
  if (failure) throw failure;
  return 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  runStack().then((code) => { process.exitCode = code; }, (error) => {
    process.stderr.write(`codex-baton-stack: ${error.message}\n`);
    process.exitCode = 1;
  });
}
