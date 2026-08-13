import { readFile } from "node:fs/promises";
import os from "node:os";
import { isAbsolute, join } from "node:path";

function object(value, name) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError(`${name} must be an object`);
  return value;
}

function positiveInteger(value, fallback, name, minimum = 1) {
  const selected = value ?? fallback;
  if (!Number.isSafeInteger(selected) || selected < minimum) throw new TypeError(`${name} must be an integer of at least ${minimum}`);
  return selected;
}

function nonempty(value, name) {
  if (typeof value !== "string" || !value.trim()) throw new TypeError(`${name} must be a non-empty string`);
  return value.trim();
}

export function defaultEventSocketPath() {
  const runtime = process.env.XDG_RUNTIME_DIR;
  if (runtime) return join(runtime, "codex-events.sock");
  return join(os.homedir(), ".local", "run", "codex-events.sock");
}

function validateLocalEndpoint(endpoint, name) {
  let url;
  try {
    url = new URL(endpoint);
  } catch {
    throw new TypeError(`servers.${name}.endpoint must be a WebSocket URL`);
  }
  if (url.protocol !== "ws:") throw new TypeError(`servers.${name}.endpoint must use ws:// in the local MVP`);
  if (!["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)) {
    throw new TypeError(`servers.${name}.endpoint must be loopback; refusing ${url.hostname}`);
  }
  if (!url.port || url.pathname !== "/" || url.search || url.hash || url.username || url.password) {
    throw new TypeError(`servers.${name}.endpoint must be a bare loopback WebSocket URL with an explicit port`);
  }
  return url.href.replace(/\/$/, "");
}

export function validateConfig(raw) {
  object(raw, "config");
  const rawServers = object(raw.servers, "servers");
  const rawTargets = object(raw.targets, "targets");
  if (Object.keys(rawServers).length === 0) throw new TypeError("servers must not be empty");
  if (Object.keys(rawTargets).length === 0) throw new TypeError("targets must not be empty");

  const servers = {};
  const assignedEndpoints = new Set();
  for (const [name, value] of Object.entries(rawServers)) {
    object(value, `servers.${name}`);
    const endpoint = validateLocalEndpoint(nonempty(value.endpoint, `servers.${name}.endpoint`), name);
    if (assignedEndpoints.has(endpoint)) throw new TypeError(`app-server endpoint ${endpoint} is assigned more than once`);
    assignedEndpoints.add(endpoint);
    servers[nonempty(name, "server name")] = Object.freeze({ endpoint });
  }

  const targets = {};
  const assignedThreads = new Set();
  const assignedParticipants = new Set();
  for (const [name, value] of Object.entries(rawTargets)) {
    object(value, `targets.${name}`);
    const targetName = nonempty(name, "target name");
    const server = nonempty(value.server, `targets.${name}.server`);
    const threadId = nonempty(value.threadId, `targets.${name}.threadId`);
    if (!servers[server]) throw new TypeError(`targets.${name}.server names unknown server ${server}`);
    const assignment = `${server}\u0000${threadId}`;
    if (assignedThreads.has(assignment)) throw new TypeError(`thread ${threadId} on ${server} is assigned to more than one target`);
    assignedThreads.add(assignment);
    const participant = value.participant === undefined ? null : nonempty(value.participant, `targets.${name}.participant`);
    if (participant && assignedParticipants.has(participant)) throw new TypeError(`Baton participant ${participant} is assigned to more than one target`);
    if (participant) assignedParticipants.add(participant);
    targets[targetName] = Object.freeze({ server, threadId, participant });
  }

  let baton = null;
  if (raw.baton !== undefined) {
    const rawBaton = object(raw.baton, "baton");
    const binary = nonempty(rawBaton.binary, "baton.binary");
    const batonConfig = nonempty(rawBaton.config, "baton.config");
    if (!isAbsolute(binary)) throw new TypeError("baton.binary must be an absolute path");
    if (!isAbsolute(batonConfig)) throw new TypeError("baton.config must be an absolute path");
    baton = Object.freeze({
      binary,
      config: batonConfig,
      waitTimeoutSeconds: positiveInteger(rawBaton.waitTimeoutSeconds, 60, "baton.waitTimeoutSeconds"),
      retryMs: positiveInteger(rawBaton.retryMs, 1000, "baton.retryMs"),
    });
  }

  const eventSocket = nonempty(raw.eventSocket ?? defaultEventSocketPath(), "eventSocket");
  if (!isAbsolute(eventSocket)) throw new TypeError("eventSocket must be an absolute path");
  const config = {
    servers: Object.freeze(servers),
    targets: Object.freeze(targets),
    baton,
    eventSocket,
    dedupWindowMs: positiveInteger(raw.dedupWindowMs, 5000, "dedupWindowMs"),
    maxEventBytes: positiveInteger(raw.maxEventBytes, 64 * 1024, "maxEventBytes", 1024),
    maxDetailsBytes: positiveInteger(raw.maxDetailsBytes, 48 * 1024, "maxDetailsBytes", 256),
    maxQueuePerTarget: positiveInteger(raw.maxQueuePerTarget, 100, "maxQueuePerTarget"),
    maxQueueTotal: positiveInteger(raw.maxQueueTotal, 1000, "maxQueueTotal"),
    reconnectMinMs: positiveInteger(raw.reconnectMinMs, 500, "reconnectMinMs"),
    reconnectMaxMs: positiveInteger(raw.reconnectMaxMs, 15_000, "reconnectMaxMs"),
    startupTimeoutMs: positiveInteger(raw.startupTimeoutMs, 15_000, "startupTimeoutMs"),
  };
  if (config.maxDetailsBytes >= config.maxEventBytes) throw new TypeError("maxDetailsBytes must be smaller than maxEventBytes");
  if (config.maxQueueTotal < config.maxQueuePerTarget) throw new TypeError("maxQueueTotal must be at least maxQueuePerTarget");
  if (config.reconnectMaxMs < config.reconnectMinMs) throw new TypeError("reconnectMaxMs must be at least reconnectMinMs");
  return Object.freeze(config);
}

export async function loadConfig(path) {
  let raw;
  try {
    raw = JSON.parse(await readFile(path, "utf8"));
  } catch (error) {
    throw new Error(`cannot load config ${path}: ${error.message}`);
  }
  return validateConfig(raw);
}
