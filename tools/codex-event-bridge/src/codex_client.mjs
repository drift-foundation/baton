import { EventEmitter } from "node:events";

const OPEN = 1;

export class CodexProtocolError extends Error {
  constructor(method, rpcError) {
    super(`${method} failed (${rpcError.code}): ${rpcError.message}`);
    this.name = "CodexProtocolError";
    this.method = method;
    this.code = rpcError.code;
    this.data = rpcError.data;
  }
}

export class CodexClient extends EventEmitter {
  constructor({ name, endpoint, debug = false, logger = console, WebSocketImpl = globalThis.WebSocket, requestTimeoutMs = 30_000, maxRetainedCompletions = 64 }) {
    super();
    if (typeof WebSocketImpl !== "function") throw new Error("this Node.js release does not provide WebSocket");
    this.name = name;
    this.endpoint = endpoint;
    this.debug = debug;
    this.logger = logger;
    this.WebSocketImpl = WebSocketImpl;
    this.requestTimeoutMs = requestTimeoutMs;
    this.socket = null;
    this.connected = false;
    this.threadStatuses = new Map();
    this.subscribedThreads = new Set();
    this.nextRequestId = 1;
    this.pending = new Map();
    // W484 (finding-codex-turn-completion-race): completions that
    // arrived with no waiter installed yet, newest last, keyed by
    // thread and turn.
    //
    // Every caller installs its wait AFTER awaiting `turn/start`, so a
    // `turn/completed` delivered before that continuation runs had
    // nowhere to go: the listener was attached to an event that had
    // already been emitted, and with no prior-state check and no
    // timeout the wait simply never settled. Recording the completion
    // first turns "did I see it yet" into a question with an answer.
    this.completions = new Map();
    this.maxRetainedCompletions = maxRetainedCompletions;
  }

  statusOf(threadId) {
    return this.threadStatuses.get(threadId) ?? { type: "notLoaded" };
  }

  isIdle(threadId) {
    return this.connected && this.statusOf(threadId).type === "idle";
  }

  async connectAndInitialize() {
    if (this.connected) return;
    await this.#open();
    try {
      const result = await this.request("initialize", {
        clientInfo: { name: "codex_event_bridge", title: "Codex Event Bridge", version: "0.1.0" },
        capabilities: {
          experimentalApi: false,
          requestAttestation: false,
          optOutNotificationMethods: ["item/agentMessage/delta", "item/commandExecution/outputDelta", "item/reasoning/summaryTextDelta", "item/reasoning/textDelta"],
        },
      });
      this.notify("initialized");
      this.connected = true;
      this.emit("connected", result);
    } catch (error) {
      this.disconnect();
      throw error;
    }
  }

  async startThread({ cwd, developerInstructions }) {
    const result = await this.request("thread/start", { cwd, developerInstructions });
    if (!result?.thread?.id || !result.thread.status) throw new Error("thread/start returned an unexpected response");
    this.subscribedThreads.add(result.thread.id);
    this.#setStatus(result.thread.id, result.thread.status);
    return result;
  }

  async resume(threadId, { developerInstructions } = {}) {
    const params = { threadId };
    if (developerInstructions !== undefined) params.developerInstructions = developerInstructions;
    const result = await this.request("thread/resume", params);
    if (!result?.thread || result.thread.id !== threadId || !result.thread.status) {
      throw new Error(`thread/resume returned an unexpected response for ${threadId}`);
    }
    this.subscribedThreads.add(threadId);
    this.#setStatus(threadId, result.thread.status);
    return result;
  }

  async readThread(threadId, { includeTurns = false } = {}) {
    const result = await this.request("thread/read", { threadId, includeTurns });
    if (!result?.thread || result.thread.id !== threadId || !result.thread.status) {
      throw new Error(`thread/read returned an unexpected response for ${threadId}`);
    }
    this.#setStatus(threadId, result.thread.status);
    return result.thread;
  }

  async hasClientMessage(threadId, clientId) {
    const thread = await this.readThread(threadId, { includeTurns: true });
    return thread.turns.some((turn) => turn.items.some((item) => item.type === "userMessage" && item.clientId === clientId));
  }

  async startTurn(threadId, text, clientUserMessageId) {
    this.#setStatus(threadId, { type: "active", activeFlags: [] });
    try {
      const result = await this.request("turn/start", {
        threadId,
        clientUserMessageId,
        input: [{ type: "text", text, text_elements: [] }],
      });
      if (!result?.turn?.id) throw new Error(`turn/start returned no turn id for ${threadId}`);
      return result.turn;
    } catch (error) {
      await this.readThread(threadId).catch(() => {});
      throw error;
    }
  }

  #completionKey(threadId, turnId) {
    return `${threadId}\u0000${turnId}`;
  }

  #retainCompletion(params) {
    const turnId = params?.turn?.id;
    if (!turnId) return;
    const key = this.#completionKey(params.threadId, turnId);
    // Re-inserted rather than updated, so the eviction order below is
    // genuinely least-recently-received.
    this.completions.delete(key);
    this.completions.set(key, params.turn);
    // Bounded: a long-lived dispatcher completes turns forever, and a
    // cache that only grows is a leak with a helpful name. The oldest
    // unconsumed record is the one nobody came back for.
    while (this.completions.size > this.maxRetainedCompletions) {
      this.completions.delete(this.completions.keys().next().value);
    }
  }

  /** W484: the completion this waiter is for, if it already arrived.
   *  Consumed on read — one completion answers one wait, and a
   *  duplicate or an unrelated turn answers neither. */
  takeCompletion(threadId, turnId) {
    const key = this.#completionKey(threadId, turnId);
    const turn = this.completions.get(key);
    if (turn === undefined) return null;
    this.completions.delete(key);
    return turn;
  }

  waitForTurnCompletion(threadId, turnId) {
    // W484 review: the ADJACENT window. Rejecting on the `disconnected`
    // EVENT only covers a waiter that was already listening — a caller
    // that installed its wait one tick after the socket dropped saw
    // nothing, found an empty cache (disconnect clears it), and waited
    // forever. That is the same missed-event class this Work exists to
    // remove, so the connection is a state to CHECK and not only an
    // event to hear.
    //
    // Checked before the cache deliberately: a disconnect clears
    // retention, so there is nothing to find, and reading the state
    // first says why rather than leaving a bare unresolved lookup.
    if (!this.connected) {
      return Promise.reject(new Error(
        `Codex app-server disconnected before turn ${turnId} could be awaited`));
    }
    const already = this.takeCompletion(threadId, turnId);
    if (already) return Promise.resolve(already);
    return new Promise((resolve, reject) => {
      const onCompleted = (params) => {
        if (params.threadId === threadId && params.turn?.id === turnId) {
          // Consumed here too: a wait that was already listening must
          // not leave a record behind for a later wait on the same
          // turn to find.
          this.takeCompletion(threadId, turnId);
          cleanup();
          resolve(params.turn);
        }
      };
      const onDisconnected = () => {
        cleanup();
        reject(new Error(`disconnected while waiting for turn ${turnId}`));
      };
      const cleanup = () => {
        this.off("turnCompleted", onCompleted);
        this.off("disconnected", onDisconnected);
      };
      this.on("turnCompleted", onCompleted);
      this.on("disconnected", onDisconnected);
    });
  }

  request(method, params) {
    if (!this.socket || this.socket.readyState !== OPEN) return Promise.reject(new Error("Codex app-server is not connected"));
    const id = this.nextRequestId++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`${method} timed out after ${this.requestTimeoutMs}ms`));
      }, this.requestTimeoutMs);
      timer.unref?.();
      this.pending.set(id, { method, resolve, reject, timer });
      try {
        this.#send({ method, id, params });
      } catch (error) {
        clearTimeout(timer);
        this.pending.delete(id);
        reject(error);
      }
    });
  }

  notify(method, params) {
    this.#send(params === undefined ? { method } : { method, params });
  }

  disconnect() {
    const socket = this.socket;
    const wasConnected = this.connected;
    this.socket = null;
    this.connected = false;
    this.subscribedThreads.clear();
    // W484: retained completions belong to the connection that
    // delivered them. A wait installed after the socket died is
    // unsettled, and unsettled waits fail closed — resolving one from
    // a pre-disconnect record would report a turn as freshly complete
    // to a caller that has no connection to act on it.
    this.completions.clear();
    for (const threadId of this.threadStatuses.keys()) this.#setStatus(threadId, { type: "notLoaded" });
    if (socket && socket.readyState < 2) socket.close();
    this.#rejectPending(new Error("Codex app-server disconnected"));
    if (wasConnected) this.emit("disconnected");
  }

  async #open() {
    const socket = new this.WebSocketImpl(this.endpoint);
    this.socket = socket;
    socket.addEventListener("message", (event) => void this.#receive(event.data));
    socket.addEventListener("close", () => this.#closed());
    socket.addEventListener("error", (event) => this.emit("socketError", event.error ?? new Error("WebSocket error")));
    await new Promise((resolve, reject) => {
      const opened = () => {
        cleanup();
        resolve();
      };
      const failed = () => {
        cleanup();
        reject(new Error(`cannot connect to Codex app-server at ${this.endpoint}`));
      };
      const cleanup = () => {
        socket.removeEventListener("open", opened);
        socket.removeEventListener("error", failed);
        socket.removeEventListener("close", failed);
      };
      socket.addEventListener("open", opened);
      socket.addEventListener("error", failed);
      socket.addEventListener("close", failed);
    });
  }

  #send(message) {
    if (!this.socket || this.socket.readyState !== OPEN) throw new Error("Codex app-server is not connected");
    if (this.debug) this.logger.debug?.(`[${this.name}] codex -> ${JSON.stringify(message)}`);
    this.socket.send(JSON.stringify(message));
  }

  async #receive(data) {
    try {
      const value = typeof data === "string" ? data : await data.arrayBuffer?.() ?? data;
      const text = typeof value === "string" ? value : Buffer.from(value).toString("utf8");
      if (this.debug) this.logger.debug?.(`[${this.name}] codex <- ${text}`);
      const message = JSON.parse(text);
      if (Object.hasOwn(message, "id") && !Object.hasOwn(message, "method")) {
        const pending = this.pending.get(message.id);
        if (!pending) return;
        clearTimeout(pending.timer);
        this.pending.delete(message.id);
        if (message.error) pending.reject(new CodexProtocolError(pending.method, message.error));
        else pending.resolve(message.result);
        return;
      }
      if (Object.hasOwn(message, "id") && message.method) {
        this.emit("serverRequest", message);
        return;
      }
      if (message.method) this.#notification(message.method, message.params);
    } catch (error) {
      this.emit("protocolError", error);
    }
  }

  #notification(method, params) {
    const threadId = params?.threadId;
    if (method === "thread/status/changed" && threadId) {
      this.#setStatus(threadId, params.status);
    } else if (method === "turn/started" && threadId) {
      this.#setStatus(threadId, { type: "active", activeFlags: [] });
      this.emit("turnStarted", params);
    } else if (method === "turn/completed" && threadId) {
      // Recorded BEFORE the event is published, so a wait installed
      // one microtask later still finds it. A listener already
      // attached consumes it in the same tick and leaves nothing
      // behind (see `waitForTurnCompletion`).
      this.#retainCompletion(params);
      this.emit("turnCompleted", params);
    } else if (method === "item/started") {
      this.emit("itemStarted", params);
    } else if (method === "item/completed") {
      this.emit("itemCompleted", params);
    }
    this.emit("notification", { method, params });
  }

  #setStatus(threadId, status) {
    this.threadStatuses.set(threadId, status);
    this.emit("status", { threadId, status });
  }

  #closed() {
    const wasConnected = this.connected;
    this.socket = null;
    this.connected = false;
    this.subscribedThreads.clear();
    this.completions.clear();   // W484: see `disconnect`
    for (const threadId of this.threadStatuses.keys()) this.#setStatus(threadId, { type: "notLoaded" });
    this.#rejectPending(new Error("Codex app-server disconnected"));
    if (wasConnected) this.emit("disconnected");
  }

  #rejectPending(error) {
    for (const pending of this.pending.values()) {
      clearTimeout(pending.timer);
      pending.reject(error);
    }
    this.pending.clear();
  }
}
