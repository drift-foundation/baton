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
  constructor({ name, endpoint, debug = false, logger = console, WebSocketImpl = globalThis.WebSocket, requestTimeoutMs = 30_000 }) {
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

  async resume(threadId) {
    const result = await this.request("thread/resume", { threadId });
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

  waitForTurnCompletion(threadId, turnId) {
    return new Promise((resolve, reject) => {
      const onCompleted = (params) => {
        if (params.threadId === threadId && params.turn?.id === turnId) {
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
