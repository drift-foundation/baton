import { readFile } from "node:fs/promises";
import os from "node:os";
import { dirname, isAbsolute, join } from "node:path";

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
    let identity = null;
    if (value.identity !== undefined) {
      const rawIdentity = object(value.identity, `targets.${name}.identity`);
      const participant = nonempty(rawIdentity.participant, `targets.${name}.identity.participant`);
      if (!/^[^.\s]+\.[^.\s]+$/.test(participant)) throw new TypeError(`targets.${name}.identity.participant must be team.member`);
      if (assignedParticipants.has(participant)) throw new TypeError(`Baton participant ${participant} is assigned to more than one target`);
      assignedParticipants.add(participant);
      // W101: the launch role is ALWAYS explicit. Inferring it meant a
      // participant gaining a second role later silently changed the
      // persona of every session started for them.
      const role = nonempty(rawIdentity.role, `targets.${name}.identity.role`);
      // W93 R9: the participant who owes this runner's interactive
      // answers. The authority accepts it here and REQUIRES it for a
      // durable incident; without it a `waiting-input` state can never
      // become the ruled actionable Inbox entry. Never guessed — and
      // since W415, required on every managed target (below).
      let actionOwner;
      if (rawIdentity.actionOwner !== undefined) {
        actionOwner = nonempty(rawIdentity.actionOwner, `targets.${name}.identity.actionOwner`);
        if (!/^[^.\s]+\.[^.\s]+$/.test(actionOwner)) throw new TypeError(`targets.${name}.identity.actionOwner must be team.member`);
      }
      if (!/^[^.\s]+$/.test(role)) throw new TypeError(`targets.${name}.identity.role must be one role handle without whitespace or dots`);
      identity = Object.freeze({ participant, role, actionOwner });
    }
    targets[targetName] = Object.freeze({ server, threadId, identity });
  }

  let roleInstructions = null;
  if (raw.roleInstructions !== undefined) {
    const source = object(raw.roleInstructions, "roleInstructions");
    const binary = nonempty(source.binary, "roleInstructions.binary");
    const batonConfig = nonempty(source.config, "roleInstructions.config");
    if (!isAbsolute(binary)) throw new TypeError("roleInstructions.binary must be an absolute path");
    if (!isAbsolute(batonConfig)) throw new TypeError("roleInstructions.config must be an absolute path");
    // W415: the DEPLOYMENT-OWNED exact command policy that authorizes a
    // managed turn's canonical Baton operations.
    //
    // Three earlier shapes were rejected — an approval policy, a
    // writable coordination-home root, and a narrowed version of that
    // root — and the approver ruled out arbitrary per-thread overrides
    // entirely. What remains is an execpolicy file the OPERATOR
    // installs; this bridge only reads and verifies it. See
    // `src/exec_policy.mjs` for why command policy is the only shape
    // that can be narrow here.
    const execPolicyFile = nonempty(source.execPolicyFile,
      "roleInstructions.execPolicyFile");
    if (!isAbsolute(execPolicyFile)) {
      throw new TypeError("roleInstructions.execPolicyFile must be an absolute path");
    }
    roleInstructions = Object.freeze({ binary, config: batonConfig,
      execPolicyFile });
    const missing = Object.entries(targets).filter(([, target]) => target.identity === null).map(([name]) => name);
    if (missing.length > 0) throw new TypeError(`roleInstructions requires an identity on every target; missing ${missing.join(", ")}`);
    // W415: durable incidents are owed to a CONFIGURED action owner and
    // the authority refuses an ownerless one. A deployment that runs
    // managed turns without naming an owner cannot produce the sticky
    // incident this Work exists to create — and the deployment that
    // reproduced the defect was exactly that deployment. So it fails
    // validation here rather than warning into a background log, which
    // is the invisibility being fixed.
    const ownerless = Object.entries(targets)
      .filter(([, target]) => target.identity && !target.identity.actionOwner)
      .map(([name]) => name);
    if (ownerless.length > 0) {
      throw new TypeError(
        `every managed target needs identity.actionOwner so a failed turn `
        + `can raise a durable incident somebody owes; missing on `
        + `${ownerless.join(", ")}`);
    }
  } else {
    const configured = Object.entries(targets).filter(([, target]) => target.identity !== null).map(([name]) => name);
    if (configured.length > 0) throw new TypeError(`target identities require roleInstructions; configured ${configured.join(", ")}`);
  }

  const eventSocket = nonempty(raw.eventSocket ?? defaultEventSocketPath(), "eventSocket");
  if (!isAbsolute(eventSocket)) throw new TypeError("eventSocket must be an absolute path");
  // W99 review P1: where the RESTART-DURABLE approval quarantine lives.
  //
  // It defaults beside the event socket because that directory is already
  // this dispatcher's own private runtime area — `start()` creates it 0700
  // — so every existing deployment gets a fence that survives a
  // dispatcher-only restart with no configuration change. It is not
  // optional: a fence an operator can switch off is not a fence.
  const quarantineDir = nonempty(
    raw.quarantineDir ?? join(dirname(eventSocket), ".codex-quarantine"),
    "quarantineDir");
  if (!isAbsolute(quarantineDir)) throw new TypeError("quarantineDir must be an absolute path");
  const config = {
    servers: Object.freeze(servers),
    targets: Object.freeze(targets),
    roleInstructions,
    eventSocket,
    quarantineDir,
    dedupWindowMs: positiveInteger(raw.dedupWindowMs, 5000, "dedupWindowMs"),
    maxEventBytes: positiveInteger(raw.maxEventBytes, 64 * 1024, "maxEventBytes", 1024),
    maxDetailsBytes: positiveInteger(raw.maxDetailsBytes, 48 * 1024, "maxDetailsBytes", 256),
    maxQueuePerTarget: positiveInteger(raw.maxQueuePerTarget, 100, "maxQueuePerTarget"),
    maxQueueTotal: positiveInteger(raw.maxQueueTotal, 1000, "maxQueueTotal"),
    reconnectMinMs: positiveInteger(raw.reconnectMinMs, 500, "reconnectMinMs"),
    reconnectMaxMs: positiveInteger(raw.reconnectMaxMs, 15_000, "reconnectMaxMs"),
    startupTimeoutMs: positiveInteger(raw.startupTimeoutMs, 15_000, "startupTimeoutMs"),
    // W3243: how long a dispatcher-owned turn may stay blocked on an
    // approval this bridge will never give before the turn is
    // interrupted. Readiness delivery is non-interactive, so the wait
    // is BOUNDED — the denial goes out immediately and this is only
    // the grace the app-server gets to end the turn by itself.
    approvalRecoveryMs: positiveInteger(raw.approvalRecoveryMs, 15_000, "approvalRecoveryMs"),
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
