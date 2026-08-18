import { EventEmitter } from "node:events";
import { chmod, lstat, mkdir, unlink } from "node:fs/promises";
import net from "node:net";
import { dirname } from "node:path";
import { CodexClient, CodexProtocolError } from "./codex_client.mjs";
import { eventFingerprint, formatEventMessage, normalizeEvent } from "./event_types.mjs";

function wait(ms, signal) {
  if (signal.aborted) return Promise.resolve();
  return new Promise((resolve) => {
    const timer = setTimeout(done, ms);
    timer.unref?.();
    signal.addEventListener("abort", done, { once: true });
    function done() {
      clearTimeout(timer);
      signal.removeEventListener("abort", done);
      resolve();
    }
  });
}

function jitter(ms) {
  return Math.max(1, Math.round(ms * (0.75 + Math.random() * 0.5)));
}

function findClientMessage(thread, clientId) {
  for (const turn of thread.turns ?? []) {
    const item = turn.items?.find((candidate) => candidate.type === "userMessage" && candidate.clientId === clientId);
    if (item) return { turn, item };
  }
  return null;
}

async function socketIsActive(path) {
  return await new Promise((resolve, reject) => {
    const probe = net.createConnection(path);
    probe.once("connect", () => {
      probe.end();
      resolve(true);
    });
    probe.once("error", (error) => {
      if (error.code === "ECONNREFUSED" || error.code === "ENOENT") resolve(false);
      else reject(error);
    });
  });
}

async function prepareSocketPath(path) {
  let stat;
  try {
    stat = await lstat(path);
  } catch (error) {
    if (error.code === "ENOENT") return;
    throw error;
  }
  if (!stat.isSocket()) throw new Error(`refusing to replace non-socket path: ${path}`);
  if (await socketIsActive(path)) throw new Error(`another event bridge is already listening at ${path}`);
  await unlink(path);
}

export class EventBridge extends EventEmitter {
  constructor({ config, debug = false, logger = console, clientFactory }) {
    super();
    this.config = config;
    this.logger = logger;
    this.server = null;
    this.ownsSocket = false;
    this.stopping = false;
    this.stopController = new AbortController();
    this.connectionTasks = [];
    this.globalQueueDepth = 0;
    this.targetByThread = new Map();
    this.targetStates = new Map();
    this.serverStates = new Map();

    const createClient = clientFactory ?? ((name, server) => new CodexClient({ name, endpoint: server.endpoint, debug, logger }));
    for (const [name, server] of Object.entries(config.servers)) {
      const client = createClient(name, server);
      const state = { name, config: server, client, targets: [], overloadDelayMs: config.reconnectMinMs, retryUntil: 0 };
      this.serverStates.set(name, state);
      this.#bindClient(state);
    }
    for (const [name, target] of Object.entries(config.targets)) {
      const state = {
        name,
        serverName: target.server,
        threadId: target.threadId,
        developerInstructions: target.developerInstructions,
        queue: [],
        recent: new Map(),
        status: { type: "notLoaded" },
        activeTurn: null,
        completedTurns: new Map(),
        draining: false,
        retryMs: config.reconnectMinMs,
        retryTimer: null,
        reconcileTimer: null,
      };
      this.targetStates.set(name, state);
      this.serverStates.get(target.server).targets.push(state);
      this.targetByThread.set(`${target.server}\u0000${target.threadId}`, state);
    }
  }

  async start({ listen = true } = {}) {
    if (listen) {
      await mkdir(dirname(this.config.eventSocket), { recursive: true, mode: 0o700 });
      await prepareSocketPath(this.config.eventSocket);
      this.server = net.createServer((socket) => this.#accept(socket));
      await new Promise((resolve, reject) => {
        this.server.once("error", reject);
        this.server.listen(this.config.eventSocket, () => {
          this.server.off("error", reject);
          resolve();
        });
      });
      await chmod(this.config.eventSocket, 0o600);
      this.ownsSocket = true;
      this.logger.info(`event receiver listening: ${this.config.eventSocket}`);
    }
    for (const serverState of this.serverStates.values()) {
      const task = this.#connectionLoop(serverState);
      this.connectionTasks.push(task);
    }
  }

  enqueue(raw) {
    let event;
    try {
      event = normalizeEvent(raw, { maxDetailsBytes: this.config.maxDetailsBytes });
    } catch (error) {
      return { accepted: false, reason: "invalid-event", error: error.message, globalQueueDepth: this.globalQueueDepth };
    }
    const state = this.targetStates.get(event.target);
    if (!state) return { accepted: false, reason: "unknown-target", target: event.target, globalQueueDepth: this.globalQueueDepth };
    if (Buffer.byteLength(JSON.stringify(event), "utf8") > this.config.maxEventBytes) {
      return { accepted: false, reason: "event-too-large", target: event.target, globalQueueDepth: this.globalQueueDepth };
    }

    const now = Date.now();
    for (const [fingerprint, seenAt] of state.recent) {
      if (now - seenAt > this.config.dedupWindowMs) state.recent.delete(fingerprint);
    }
    const fingerprint = eventFingerprint(event);
    const seenAt = state.recent.get(fingerprint);
    if (seenAt !== undefined && now - seenAt <= this.config.dedupWindowMs) {
      this.logger.info(`[${event.target}] duplicate event suppressed: ${event.type}`);
      return { accepted: false, reason: "duplicate", target: event.target, queueDepth: state.queue.length, globalQueueDepth: this.globalQueueDepth };
    }
    if (state.queue.length >= this.config.maxQueuePerTarget) {
      return { accepted: false, reason: "target-queue-full", target: event.target, queueDepth: state.queue.length, globalQueueDepth: this.globalQueueDepth };
    }
    if (this.globalQueueDepth >= this.config.maxQueueTotal) {
      return { accepted: false, reason: "global-queue-full", target: event.target, queueDepth: state.queue.length, globalQueueDepth: this.globalQueueDepth };
    }

    state.recent.set(fingerprint, now);
    state.queue.push({ event, ambiguous: false });
    this.globalQueueDepth += 1;
    this.logger.info(`[${event.target}] event received: ${event.type}`);
    if (state.status.type !== "idle") this.logger.info(`[${event.target}] unavailable or active; queued (${state.queue.length})`);
    void this.#drain(state);
    return { accepted: true, reason: "queued", target: event.target, eventId: event.id, queueDepth: state.queue.length, globalQueueDepth: this.globalQueueDepth };
  }

  statusSnapshot() {
    const targets = {};
    let ready = true;
    for (const [name, state] of this.targetStates) {
      const connected = this.serverStates.get(state.serverName).client.connected;
      const loaded = connected && state.status.type !== "notLoaded";
      if (!loaded) ready = false;
      targets[name] = Object.freeze({ connected, loaded, status: state.status.type });
    }
    return Object.freeze({ ready, targets: Object.freeze(targets), globalQueueDepth: this.globalQueueDepth });
  }

  handleRequest(payload) {
    return payload?.control === "status" ? this.statusSnapshot() : this.enqueue(payload);
  }

  async stop() {
    if (this.stopping) return;
    this.stopping = true;
    this.stopController.abort();
    for (const state of this.targetStates.values()) {
      if (state.retryTimer) clearTimeout(state.retryTimer);
      if (state.reconcileTimer) clearTimeout(state.reconcileTimer);
    }
    for (const serverState of this.serverStates.values()) serverState.client.disconnect();
    if (this.server) {
      await new Promise((resolve) => this.server.close(resolve));
      this.server = null;
    }
    if (this.ownsSocket) {
      try {
        const stat = await lstat(this.config.eventSocket);
        if (stat.isSocket()) await unlink(this.config.eventSocket);
      } catch (error) {
        if (error.code !== "ENOENT") throw error;
      }
      this.ownsSocket = false;
    }
    await Promise.allSettled(this.connectionTasks);
  }

  async #drain(state) {
    if (this.stopping || state.draining || state.activeTurn || state.queue.length === 0 || state.status.type !== "idle") return;
    const serverState = this.serverStates.get(state.serverName);
    if (!serverState.client.connected) return;
    const serverDelay = serverState.retryUntil - Date.now();
    if (serverDelay > 0) {
      this.#scheduleDrain(state, serverDelay);
      return;
    }

    state.draining = true;
    const queued = state.queue[0];
    try {
      if (queued.ambiguous) {
        const delivered = await this.#reconcileAmbiguous(state, queued);
        if (delivered) return;
      }
      const turn = await serverState.client.startTurn(state.threadId, formatEventMessage(queued.event), queued.event.id);
      this.#dequeue(state);
      const completed = state.completedTurns.get(turn.id);
      if (completed) {
        state.completedTurns.delete(turn.id);
        state.activeTurn = null;
        this.logger.info(`[${state.name}] turn completed before acceptance was observed: ${turn.id} (${completed.status})`);
      } else {
        state.activeTurn = { id: turn.id, event: queued.event };
      }
      state.retryMs = this.config.reconnectMinMs;
      serverState.overloadDelayMs = this.config.reconnectMinMs;
      serverState.retryUntil = 0;
      this.emit("turnAccepted", { target: state.name, turnId: turn.id, event: queued.event });
    } catch (error) {
      queued.ambiguous = !(error instanceof CodexProtocolError);
      if (error instanceof CodexProtocolError && error.code === -32001) {
        const retry = jitter(serverState.overloadDelayMs);
        serverState.retryUntil = Date.now() + retry;
        serverState.overloadDelayMs = Math.min(this.config.reconnectMaxMs, serverState.overloadDelayMs * 2);
        this.logger.warn(`[${state.name}] app-server overloaded; event retained, retrying after ${retry}ms`);
        for (const target of serverState.targets) this.#scheduleDrain(target, retry);
      } else {
        this.logger.warn(`[${state.name}] event retained; turn/start failed: ${error.message}`);
        if (serverState.client.connected) {
          await this.#reconcileTarget(state).catch((reconcileError) => {
            this.logger.warn(`[${state.name}] reconciliation failed: ${reconcileError.message}`);
            this.#scheduleReconcile(state, jitter(state.retryMs));
          });
          this.#scheduleDrain(state, jitter(state.retryMs));
          state.retryMs = Math.min(this.config.reconnectMaxMs, state.retryMs * 2);
        }
      }
    } finally {
      state.draining = false;
      if (!state.activeTurn && state.status.type === "idle" && state.queue.length > 0) this.#scheduleDrain(state, 0);
    }
  }

  async #reconcileAmbiguous(state, queued) {
    const client = this.serverStates.get(state.serverName).client;
    const thread = await client.readThread(state.threadId, { includeTurns: true });
    const delivered = findClientMessage(thread, queued.event.id);
    if (!delivered) {
      queued.ambiguous = false;
      return false;
    }
    this.#dequeue(state);
    if (delivered.turn.status === "inProgress") state.activeTurn = { id: delivered.turn.id, event: queued.event };
    this.logger.warn(`[${state.name}] reconciled ambiguous turn/start as delivered: ${delivered.turn.id} (${delivered.turn.status})`);
    return true;
  }

  async #reconcileTarget(state) {
    const client = this.serverStates.get(state.serverName).client;
    const response = await client.resume(state.threadId, {
      developerInstructions: state.developerInstructions,
    });
    state.status = response.thread.status;

    if (state.queue[0]?.ambiguous) {
      const delivered = findClientMessage(response.thread, state.queue[0].event.id);
      if (delivered) {
        const event = state.queue[0].event;
        this.#dequeue(state);
        state.activeTurn = delivered.turn.status === "inProgress" ? { id: delivered.turn.id, event } : null;
        this.logger.warn(`[${state.name}] reconciled ambiguous turn/start as delivered: ${delivered.turn.id} (${delivered.turn.status})`);
      }
    }

    if (state.activeTurn) {
      const persisted = response.thread.turns?.find((turn) => turn.id === state.activeTurn.id);
      if (persisted && persisted.status !== "inProgress") {
        this.logger.info(`[${state.name}] reconciled turn completion: ${persisted.id} (${persisted.status})`);
        state.activeTurn = null;
      } else if (!persisted && response.thread.status.type === "idle") {
        this.logger.warn(`[${state.name}] accepted turn ${state.activeTurn.id} is absent after resume; clearing local in-flight state without replay`);
        state.activeTurn = null;
      }
    }
    this.logger.info(`[${state.name}] thread resumed: ${state.threadId} (${state.status.type})`);
    void this.#drain(state);
  }

  #dequeue(state) {
    state.queue.shift();
    this.globalQueueDepth -= 1;
  }

  #scheduleDrain(state, delayMs) {
    if (this.stopping || state.retryTimer) return;
    state.retryTimer = setTimeout(() => {
      state.retryTimer = null;
      void this.#drain(state);
    }, Math.max(0, delayMs));
    state.retryTimer.unref?.();
  }

  #scheduleReconcile(state, delayMs) {
    if (this.stopping || state.reconcileTimer) return;
    state.reconcileTimer = setTimeout(async () => {
      state.reconcileTimer = null;
      const client = this.serverStates.get(state.serverName).client;
      if (!client.connected) return;
      try {
        await this.#reconcileTarget(state);
        state.retryMs = this.config.reconnectMinMs;
      } catch (error) {
        this.logger.warn(`[${state.name}] thread resume retry failed: ${error.message}`);
        this.#scheduleReconcile(state, jitter(state.retryMs));
        state.retryMs = Math.min(this.config.reconnectMaxMs, state.retryMs * 2);
      }
    }, Math.max(0, delayMs));
    state.reconcileTimer.unref?.();
  }

  #bindClient(serverState) {
    const { client } = serverState;
    client.on("connected", () => this.logger.info(`[${serverState.name}] connected to Codex app-server`));
    client.on("disconnected", () => {
      this.logger.warn(`[${serverState.name}] Codex app-server disconnected; queued events retained`);
      for (const target of serverState.targets) target.status = { type: "notLoaded" };
    });
    client.on("status", ({ threadId, status }) => {
      const state = this.targetByThread.get(`${serverState.name}\u0000${threadId}`);
      if (!state) return;
      state.status = status;
      if (status.type === "idle") void this.#drain(state);
    });
    client.on("turnStarted", ({ threadId, turn }) => {
      const state = this.targetByThread.get(`${serverState.name}\u0000${threadId}`);
      if (state) this.logger.info(`[${state.name}] turn started: ${turn.id}`);
    });
    client.on("turnCompleted", (params) => void this.#turnCompleted(serverState, params));
    client.on("serverRequest", (request) => {
      const threadId = request.params?.threadId;
      const state = threadId ? this.targetByThread.get(`${serverState.name}\u0000${threadId}`) : null;
      const scope = state ? `[${state.name}]` : `[${serverState.name}]`;
      this.logger.warn(`${scope} Codex requires interactive handling for ${request.method} (request ${request.id}); the bridge will not approve or answer it`);
      this.emit("serverRequest", { server: serverState.name, target: state?.name ?? null, request });
    });
    client.on("protocolError", (error) => this.logger.error(`[${serverState.name}] Codex protocol error: ${error.message}`));
  }

  async #turnCompleted(serverState, params) {
    const state = this.targetByThread.get(`${serverState.name}\u0000${params.threadId}`);
    if (!state) return;
    const isExternal = state.activeTurn?.id === params.turn.id;
    this.logger.info(`[${state.name}] turn completed: ${params.turn.id} (${params.turn.status})${isExternal ? "" : " [interactive]"}`);
    if (isExternal) state.activeTurn = null;
    else {
      state.completedTurns.set(params.turn.id, params.turn);
      while (state.completedTurns.size > 20) state.completedTurns.delete(state.completedTurns.keys().next().value);
    }
    try {
      const thread = await serverState.client.readThread(state.threadId);
      state.status = thread.status;
    } catch (error) {
      this.logger.warn(`[${state.name}] could not refresh thread status: ${error.message}`);
    }
    void this.#drain(state);
  }

  async #connectionLoop(serverState) {
    let retryMs = this.config.reconnectMinMs;
    while (!this.stopping) {
      try {
        await serverState.client.connectAndInitialize();
        retryMs = this.config.reconnectMinMs;
        for (const target of serverState.targets) {
          try {
            await this.#reconcileTarget(target);
          } catch (error) {
            target.status = { type: "notLoaded" };
            this.logger.warn(`[${target.name}] thread resume failed: ${error.message}`);
            this.#scheduleReconcile(target, jitter(target.retryMs));
          }
        }
        if (serverState.client.connected) await new Promise((resolve) => serverState.client.once("disconnected", resolve));
      } catch (error) {
        if (!this.stopping) this.logger.warn(`[${serverState.name}] Codex connection failed: ${error.message}; retrying in ${retryMs}ms`);
      }
      if (!this.stopping) {
        await wait(jitter(retryMs), this.stopController.signal);
        retryMs = Math.min(this.config.reconnectMaxMs, retryMs * 2);
      }
    }
  }

  #accept(socket) {
    socket.setEncoding("utf8");
    let buffer = "";
    let answered = false;
    const answer = (payload) => {
      if (answered) return;
      answered = true;
      socket.end(`${JSON.stringify(payload)}\n`);
    };
    socket.on("data", (chunk) => {
      buffer += chunk;
      if (Buffer.byteLength(buffer, "utf8") > this.config.maxEventBytes) {
        answer({ accepted: false, reason: "event-too-large", globalQueueDepth: this.globalQueueDepth });
        return;
      }
      const newline = buffer.indexOf("\n");
      if (newline === -1) return;
      try {
        answer(this.handleRequest(JSON.parse(buffer.slice(0, newline))));
      } catch (error) {
        answer({ accepted: false, reason: "invalid-event", error: error.message, globalQueueDepth: this.globalQueueDepth });
      }
    });
    socket.on("end", () => {
      if (!answered && buffer.trim()) {
        try {
          answer(this.handleRequest(JSON.parse(buffer)));
        } catch (error) {
          answer({ accepted: false, reason: "invalid-event", error: error.message, globalQueueDepth: this.globalQueueDepth });
        }
      }
    });
    socket.on("error", (error) => this.logger.warn(`event socket client error: ${error.message}`));
  }
}
