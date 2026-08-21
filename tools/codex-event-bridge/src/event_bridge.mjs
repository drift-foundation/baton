import { execFile } from "node:child_process";
import { EventEmitter } from "node:events";
import { chmod, lstat, mkdir, unlink } from "node:fs/promises";
import net from "node:net";
import { dirname } from "node:path";
import { CodexClient, CodexProtocolError } from "./codex_client.mjs";
import { classifyFailure, makeRuntimePublisher, silentPublisher } from "./runtime_publisher.mjs";
import { eventFingerprint, formatEventMessage, normalizeEvent } from "./event_types.mjs";
import { assertPolicyProvisioned } from "./exec_policy.mjs";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

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
  // W93 slice 4: `runtimeFactory` builds one runtime-lease publisher
  // per identified target. Injectable so tests pin the exact
  // transitions; defaulted so a deployment that already configures
  // `roleInstructions` plus a target identity gets it with no new
  // configuration at all — those are precisely the three facts a
  // publisher needs.
  constructor({ config, debug = false, logger = console, clientFactory, runtimeFactory, revalidate }) {
    super();
    this.config = config;
    this.logger = logger;
    // W1224: the one read that revalidates a queued episode. Injected
    // in tests, and the ordinary public CLI invocation otherwise —
    // the same shape every other Baton call in this package uses.
    this.revalidate = revalidate ?? ((file, args) => execFileAsync(
      file, args, { encoding: "utf8", maxBuffer: 4 * 1024 * 1024 }));
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
        // W3243: the approval this target is wedged on, or null. Set
        // when a server-initiated request arrives and cleared only when
        // the turn actually ends — so "unhealthy" describes a live
        // condition rather than a log line that scrolled past.
        blocked: null,
        blockedTimer: null,
        draining: false,
        retryMs: config.reconnectMinMs,
        retryTimer: null,
        reconcileTimer: null,
        // The runner state for the participant this target IS. A
        // target with no configured identity has no participant to
        // report as, so it gets the silent publisher rather than a
        // guess.
        runtime: (runtimeFactory ?? defaultRuntimeFactory)(config, target,
                                                           logger),
        identity: target.identity,
      };
      this.targetStates.set(name, state);
      this.serverStates.get(target.server).targets.push(state);
      this.targetByThread.set(`${target.server}\u0000${target.threadId}`, state);
    }
  }

  async start({ listen = true } = {}) {
    // W415: BEFORE anything opens, PREFLIGHT the nominated execution
    // policy. A dispatcher whose turns escalate for approval on every
    // claim is the defect this Work records, and it must not open leases
    // and report itself healthy while in that state.
    //
    // This checks the file the deployment nominates. It is not a
    // measurement of the policy the app-server actually loaded — Codex
    // may read other sources — so a green preflight means "the
    // deployment nominated a correct policy", not "the effective
    // boundary is correct". The live matrix in
    // `smoke/exact_policy_matrix.mjs` establishes the latter.
    if (this.config.roleInstructions?.execPolicyFile) {
      for (const state of this.targetStates.values()) {
        if (!state.identity) continue;
        assertPolicyProvisioned(this.config.roleInstructions.execPolicyFile, {
          binary: this.config.roleInstructions.binary,
          config: this.config.roleInstructions.config,
          participant: state.identity.participant,
        });
      }
    }
    // W93: every identified target's lease opens here, so a configured
    // participant whose runner is up but quiet is visibly present
    // rather than indistinguishable from one that never started.
    for (const state of this.targetStates.values()) {
      void state.runtime.start({ session: state.threadId });
      // W93 R17: what this dispatcher actually knows about the runner
      // it drives, published without inference and without a provider
      // call — its own process identity, the target it dispatches
      // through, and the socket it listens on. Anything it cannot
      // observe stays absent rather than guessed.
      void state.runtime.facts({
        service: `codex-event-bridge pid ${process.pid}`,
        dispatcher: `${state.serverName}/${state.name}`,
        readiness: this.config.eventSocket,
      }, { source: "configured" });
    }
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
    // W3243: `queuedAt` is what makes "how long has delivery been
    // stuck" answerable. 24 events queued behind one turn was the
    // incident, and the depth alone did not say for how long.
    state.queue.push({ event, ambiguous: false, queuedAt: now });
    this.globalQueueDepth += 1;
    this.logger.info(`[${event.target}] event received: ${event.type}`);
    if (state.status.type !== "idle") this.logger.info(`[${event.target}] unavailable or active; queued (${state.queue.length})`);
    void this.#drain(state);
    return { accepted: true, reason: "queued", target: event.target, eventId: event.id, queueDepth: state.queue.length, globalQueueDepth: this.globalQueueDepth };
  }

  statusSnapshot() {
    const targets = {};
    let ready = true;
    const now = Date.now();
    for (const [name, state] of this.targetStates) {
      const connected = this.serverStates.get(state.serverName).client.connected;
      const loaded = connected && state.status.type !== "notLoaded";
      // W3243: LOADABLE-AND-IDLE and LOADED-BUT-UNABLE are different
      // answers, and the incident is exactly the second one — the
      // target was connected and loaded, so the stack reported it
      // healthy while it could not accept a single delivery. A target
      // wedged on an approval this bridge will never give is not
      // ready, and neither is the stack.
      const blocked = state.blocked;
      if (!loaded || blocked) ready = false;
      const oldest = state.queue.length ? state.queue[0].queuedAt : null;
      targets[name] = Object.freeze({
        connected,
        loaded,
        status: state.status.type,
        // Everything an operator needs to act without reading a log:
        // who this target is, which Thread and turn are stuck, why,
        // how much is waiting behind it, and for how long.
        deliverable: Boolean(loaded && !blocked),
        participant: state.identity?.participant ?? null,
        threadId: state.threadId,
        queueDepth: state.queue.length,
        oldestQueuedMs: oldest === null ? null : Math.max(0, now - oldest),
        blocked: blocked
          ? Object.freeze({
            turnId: blocked.turnId,
            cause: blocked.cause,
            method: blocked.method,
            since: blocked.since,
            ageMs: Math.max(0, now - blocked.since),
            denied: blocked.denied,
            interrupted: blocked.interrupted,
          })
          : null,
      });
    }
    return Object.freeze({ ready, targets: Object.freeze(targets), globalQueueDepth: this.globalQueueDepth });
  }

  handleRequest(payload) {
    if (payload?.control === "status") return this.statusSnapshot();
    // W93 R21: the ONE path a refresh takes, and it stops here. It
    // never reaches `enqueue`, so it cannot become a queued message,
    // a turn, or a model wake — the difference between this control
    // and an event is the whole point of the entry declaring
    // `wakes_model: false`.
    if (payload?.control === "runtime-refresh") return this.answerRefresh(payload);
    return this.enqueue(payload);
  }

  // The lease owner republishes what it already holds: its own process
  // identity, the target it dispatches through, and the socket it
  // listens on. No provider call, no model turn, nothing inferred —
  // the same three facts it published at startup, observed again now.
  async answerRefresh(request) {
    const state = this.targetStates.get(request.target);
    if (!state) {
      return { accepted: false, reason: "unknown-target", target: request.target ?? null };
    }
    // A dispatcher answers for the participant it IS. Publishing facts
    // under somebody else's identity because a message asked would
    // make the roster lie in exactly the way this slice exists to
    // prevent.
    const mine = state.identity?.participant ?? null;
    if (!mine || (request.participant && request.participant !== mine)) {
      this.logger.warn(`[${state.name}] refusing a runtime refresh addressed to ${request.participant ?? "nobody"}; this target reports as ${mine ?? "no participant"}`);
      return { accepted: false, reason: "foreign-participant", target: state.name, participant: mine };
    }
    // R25: the exact generation is answered, so a publication cannot
    // retire a question asked after the one it was made for.
    const published = await state.runtime.facts({
      service: `codex-event-bridge pid ${process.pid}`,
      dispatcher: `${state.serverName}/${state.name}`,
      readiness: this.config.eventSocket,
    }, { source: "configured", answers: request.generation });
    this.logger.info(`[${state.name}] runtime refresh answered from held facts${published ? "" : " (publication failed; the request stands)"}`);
    // A failed publication is NOT accepted: the request is still
    // outstanding, and telling the producer otherwise would retire the
    // one retry the level-triggered signal gives us.
    return { accepted: Boolean(published), reason: published ? "runtime-refresh" : "runtime-refresh-failed",
             target: state.name, participant: mine,
             generation: request.generation ?? null,
             requested_at: request.requested_at ?? null };
  }

  async stop() {
    if (this.stopping) return;
    this.stopping = true;
    // The explicit goodbye: `offline` by report rather than by expiry,
    // which is a different operational fact and gets different
    // provenance.
    for (const state of this.targetStates.values()) {
      // R10: a clean shutdown carries NO cause — a runner that exited
      // cleanly did not fail.
      void state.runtime.end({ detail: "codex dispatcher stopped" });
    }
    this.stopController.abort();
    for (const state of this.targetStates.values()) {
      if (state.retryTimer) clearTimeout(state.retryTimer);
      if (state.reconcileTimer) clearTimeout(state.reconcileTimer);
      // W3243 review P2: `stop()` owns EVERY timer this bridge starts.
      // A recovery callback surviving shutdown would interrupt through
      // a disconnected client and publish a failure caused by nothing
      // but the shutdown that failed to cancel its own timer — after
      // the runtime already reported a clean exit.
      if (state.blockedTimer) {
        clearTimeout(state.blockedTimer);
        state.blockedTimer = null;
      }
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
    if (this.stopping || state.draining || state.activeTurn || state.blocked || state.queue.length === 0 || state.status.type !== "idle") return;
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
      // W1224: the LAST thing before a model turn is spent. A v11
      // readiness event can sit in this queue behind a running turn,
      // and by the time it drains the Work may have been passed to
      // another endpoint — which is exactly how a reviewer was woken
      // for an implementer's queued Work, with canonical `detail`
      // disagreeing at the same instant.
      //
      // The check is a cheap read of the SAME participant's own
      // projection, requiring this exact episode key to still be
      // there. It narrows the window rather than closing it — a
      // mutation can still land between the read and the turn — so
      // the agent's atomic claim remains the final authority. What it
      // removes is the misleading wake, not the refusal behind it.
      if (await this.#episodeIsOver(state, queued.event)) {
        this.#dequeue(state);
        this.logger.info(`[${state.name}] ${queued.event.action.key} is no longer actionable for ${queued.event.action.participant}; dropped without spending a turn`);
        this.emit("actionDropped", { target: state.name, event: queued.event });
        if (state.queue.length > 0) this.#scheduleDrain(state, 0);
        return;
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

  /** W1224: is this queued readiness event's episode gone?
   *
   *  `false` for anything this dispatcher cannot check — an event
   *  with no action block, a deployment with no `roleInstructions` to
   *  reach Baton through, or a read that fails. A revalidation that
   *  cannot run must not silently discard a wake; the event is
   *  retained and the ordinary retry decides. Only a SUCCESSFUL read
   *  that does not list the key drops it. */
  async #episodeIsOver(state, event) {
    const action = event.action;
    if (!action) return false;
    // W1224 review: the canonical read proves the episode is live for
    // the participant the EVENT names — and says nothing about whether
    // that participant is the identity this target runs as. A valid
    // event addressed to the tuner target while naming `baton.codex`
    // therefore passed, and woke the tuner session for somebody else's
    // Work. The confirmed boundary is that a readiness action reaches
    // only the participant eligible for that exact episode, so the two
    // identities must AGREE before anything else is asked.
    //
    // Structural, and checked before the read: a mismatch is not a
    // stale episode to re-examine, it is an event that was never for
    // this target.
    const mine = state.identity?.participant;
    if (mine && action.participant !== mine) {
      this.logger.warn(`[${state.name}] ${action.key} is addressed to ${action.participant}; this target runs as ${mine}. Dropped.`);
      return true;
    }
    if (!this.config.roleInstructions) return false;
    const argv = ["--config", this.config.roleInstructions.config,
                  "--participant", action.participant, "wait", "timeout=0"];
    let payload;
    try {
      const result = await this.revalidate(this.config.roleInstructions.binary, argv);
      payload = JSON.parse(result.stdout);
    } catch (error) {
      this.logger.warn(`[${state.name}] could not revalidate ${action.key}: ${error.message}; the event is retained`);
      return false;
    }
    const live = payload?.result?.actionable;
    if (!Array.isArray(live)) {
      this.logger.warn(`[${state.name}] revalidation of ${action.key} returned no actionable set; the event is retained`);
      return false;
    }
    return !live.some((entry) => entry.action_key === action.key);
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
      for (const target of serverState.targets) {
        target.status = { type: "notLoaded" };
        // A disconnect DURING shutdown is the shutdown, not a fault:
        // `stop()` has already said goodbye, and reporting a transport
        // retry after that would describe a reconnection nobody is
        // going to attempt.
        if (this.stopping) continue;
        // OBSERVED, not inferred: the transport dropped and this
        // dispatcher is about to reconnect. The runner itself may be
        // perfectly healthy, which is why this is `retrying` and not
        // `failed` — and why nothing here reports `offline`, a state
        // only an expired lease derives.
        void target.runtime.state("retrying", {
          cause: "transport",
          detail: `${serverState.name} app-server disconnected`,
        });
      }
    });
    client.on("status", ({ threadId, status }) => {
      const state = this.targetByThread.get(`${serverState.name}\u0000${threadId}`);
      if (!state) return;
      state.status = status;
      // W3243: an idle thread has no turn left to be blocked on, so the
      // wedge is over and the retained events drain.
      if (status.type === "idle") {
        this.#clearBlocked(state);
        void this.#drain(state);
      }
    });
    client.on("turnStarted", ({ threadId, turn }) => {
      const state = this.targetByThread.get(`${serverState.name}\u0000${threadId}`);
      if (!state) return;
      this.logger.info(`[${state.name}] turn started: ${turn.id}`);
      void state.runtime.state("working", { session: threadId });
    });
    client.on("turnCompleted", (params) => void this.#turnCompleted(serverState, params));
    client.on("serverRequest", (request) => {
      const threadId = request.params?.threadId;
      const state = threadId ? this.targetByThread.get(`${serverState.name}\u0000${threadId}`) : null;
      const scope = state ? `[${state.name}]` : `[${serverState.name}]`;
      this.logger.warn(`${scope} Codex requires interactive handling for ${request.method} (request ${request.id}); the bridge will not approve it`);
      // THE motivating incident. W22 read `active` with a Handler while
      // its turn sat on exactly this request, and the only evidence was
      // this log line. The dispatcher maps the request it already
      // observes into `waiting-input` and STILL does not approve it.
      void state?.runtime.state("waiting-input", {
        cause: "approval",
        detail: `${request.method} requires interactive handling`,
        session: threadId,
      });
      // W415: the live state above is correct AND transient — it is
      // supposed to vanish when the runner returns to `idle`. That is
      // what made three of these disappear without anybody learning why
      // the reviews were never picked up. The durable, Work-correlated
      // incident is filed here, beside it, and stays until its action
      // owner dismisses it. Neither substitutes for the other.
      //
      // Nothing about the request BODY is published: `#approvalCategory`
      // maps the method to a closed safe category and the detail names
      // the method only.
      if (state) {
        // The episode being served is the one whose turn is in flight.
        const action = state.activeTurn?.event?.action ?? null;
        void state.runtime.incident({
          cause: "approval",
          category: EventBridge.#approvalCategory(request.method),
          detail: `${request.method} requested interactive approval; a `
            + `dispatcher-owned readiness turn is non-interactive and `
            + `denied it`,
          work: action?.work ?? null,
          episode: action?.episode ?? null,
          actionKey: action?.key ?? null,
          session: threadId,
        });
      }
      // W3243: publishing the state was not enough. LEAVING THE REQUEST
      // UNANSWERED is what wedged the turn — it waited for a human who
      // was not in this conversation, and 24 later readiness events
      // queued behind it. A dispatcher-owned turn is NON-INTERACTIVE
      // execution, so the request is explicitly DENIED and the turn is
      // ended within a bound. Denying is not approving, and it is not
      // silence either.
      if (state) this.#denyAndRecover(serverState, state, request);
      this.emit("serverRequest", { server: serverState.name, target: state?.name ?? null, request });
    });
    client.on("protocolError", (error) => {
      this.logger.error(`[${serverState.name}] Codex protocol error: ${error.message}`);
      for (const target of serverState.targets) {
        // R8/R10: the message classifies and is then discarded. A Codex
        // protocol error can carry endpoint URLs and payload fragments,
        // and truncating that bounds the leak rather than preventing it.
        void target.runtime.state("failed", classifyFailure(error));
      }
    });
  }

  // W3243: the ruled non-interactive recovery, in order.
  //
  // 1. DENY the request explicitly, because an unanswered one is what
  //    wedges the turn. A JSON-RPC error cannot be mistaken for an
  //    approval and invents no result schema this bridge owns.
  // 2. Mark the target UNDELIVERABLE, so the stack stops reporting a
  //    target it cannot deliver to as healthy.
  // 3. Give the app-server a BOUNDED grace to end the turn itself, and
  //    interrupt it when that expires.
  //
  // What it never does is approve, answer with a decision, or start a
  // replacement context. If the interrupt cannot end the turn either,
  // the target stays visibly unhealthy and the operator restarts the
  // managed stack — whose already-approved fresh-context-per-start
  // policy supplies a clean target. V12's worker supervisor owns
  // automatic replacement.
  // W415: method -> SAFE category. The command body never leaves the
  // dispatcher, so what an operator gets is the kind of thing that was
  // refused. An unrecognised method is `other` rather than a guess.
  static #approvalCategory(method) {
    if (typeof method !== "string") return "other";
    // The app-server spells the same request two ways — `execCommandApproval`
    // and `item/commandExecution/requestApproval` — so separators are
    // folded out before matching rather than matching each spelling.
    const flat = method.replace(/[^a-z]/gi, "").toLowerCase();
    if (flat.includes("execcommandapproval")
        || flat.includes("commandexecutionrequestapproval")) {
      return "shell";
    }
    if (flat.includes("applypatchapproval")
        || flat.includes("filechangerequestapproval")) {
      return "patch";
    }
    if (flat.includes("permissionsrequestapproval")) return "file-write";
    if (flat.includes("mcp") || flat.includes("elicitation")) return "mcp";
    return "other";
  }

  #denyAndRecover(serverState, state, request) {
    const denied = serverState.client.respondError(
      request.id, -32601,
      "this Baton dispatcher runs non-interactive readiness turns and "
      + "cannot approve commands; the turn will be ended");
    this.logger.warn(
      `[${state.name}] ${denied ? "denied" : "could not deny"} `
      + `${request.method}; readiness delivery is blocked until the turn ends`);
    const turnId = this.#blockedTurnId(state, request);
    if (state.blocked) {
      state.blocked.denied = state.blocked.denied || denied;
      // A later request may carry the turn an earlier one lacked.
      if (!state.blocked.turnId && turnId) state.blocked.turnId = turnId;
      return;
    }
    state.blocked = {
      turnId,
      cause: "approval",
      method: request.method,
      since: Date.now(),
      denied,
      interrupted: false,
    };
    if (state.blockedTimer) clearTimeout(state.blockedTimer);
    state.blockedTimer = setTimeout(() => {
      state.blockedTimer = null;
      void this.#interruptBlocked(serverState, state);
    }, this.config.approvalRecoveryMs);
    state.blockedTimer.unref?.();
  }

  // W3243 review P1: the REQUEST names the turn, and that is the
  // authoritative locator.
  //
  // The app-server schema requires `params.turnId` on an approval
  // request. `state.activeTurn` is this bridge's own record and can
  // still be null when the server request races the continuation that
  // sets it — which is exactly when recovery matters, and exactly when
  // interrupting on local state would pass a null turn.
  //
  // So the request wins, and a disagreement is REPORTED rather than
  // silently resolved in either direction: two different turn ids on
  // one thread is a fact an operator needs, and picking one quietly
  // would hide it.
  #blockedTurnId(state, request) {
    const fromRequest = request?.params?.turnId;
    const named = typeof fromRequest === "string" && fromRequest
      ? fromRequest : null;
    const local = state.activeTurn?.id ?? null;
    if (named && local && named !== local) {
      this.logger.warn(
        `[${state.name}] approval names turn ${named} while this bridge `
        + `records ${local} active; recovering the turn the request names`);
    }
    if (!named && !local) {
      this.logger.warn(
        `[${state.name}] the approval request named no turn and none is `
        + `recorded; recovery cannot target one`);
    }
    return named ?? local;
  }

  async #interruptBlocked(serverState, state) {
    if (this.stopping || !state.blocked || state.blocked.interrupted) return;
    state.blocked.interrupted = true;
    const turnId = state.blocked.turnId;
    try {
      await serverState.client.interruptTurn(state.threadId, turnId);
      this.logger.warn(
        `[${state.name}] interrupted the blocked turn ${turnId ?? "(unknown)"}`);
    } catch (error) {
      // The turn could not be ended. The target stays unhealthy and
      // says so; nothing here approves anything to get moving again.
      this.logger.error(
        `[${state.name}] could not end the blocked turn: ${error.message}. `
        + `Readiness for this target is stuck (${state.queue.length} queued); `
        + `restart the managed stack to get a fresh context.`);
      void state.runtime.state("failed", {
        cause: "approval",
        detail: "a blocked turn could not be interrupted; restart the stack",
      });
    }
  }

  // W3243: the wedge is over only when the TURN is over. Called from
  // every path that observes the turn ending, so the unhealthy report
  // clears on the same fact that makes delivery possible again.
  #clearBlocked(state) {
    if (state.blockedTimer) {
      clearTimeout(state.blockedTimer);
      state.blockedTimer = null;
    }
    if (!state.blocked) return;
    this.logger.info(
      `[${state.name}] blocked turn ended; draining ${state.queue.length} `
      + `retained readiness event(s)`);
    state.blocked = null;
  }

  async #turnCompleted(serverState, params) {
    const state = this.targetByThread.get(`${serverState.name}\u0000${params.threadId}`);
    if (!state) return;
    const isExternal = state.activeTurn?.id === params.turn.id;
    this.logger.info(`[${state.name}] turn completed: ${params.turn.id} (${params.turn.status})${isExternal ? "" : " [interactive]"}`);
    // Between turns the runner is idle — the honest state, and one an
    // adapter can only report because it OBSERVED the completion.
    // Silence past the lease deadline is what becomes `unknown`, and
    // only the authority derives that.
    void state.runtime.state("idle", { session: params.threadId });
    this.#clearBlocked(state);
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
    const invalid = (error) => answer({ accepted: false, reason: "invalid-event", error: error.message, globalQueueDepth: this.globalQueueDepth });
    socket.on("data", (chunk) => {
      buffer += chunk;
      if (Buffer.byteLength(buffer, "utf8") > this.config.maxEventBytes) {
        answer({ accepted: false, reason: "event-too-large", globalQueueDepth: this.globalQueueDepth });
        return;
      }
      const newline = buffer.indexOf("\n");
      if (newline === -1) return;
      // `handleRequest` answers synchronously for events and returns
      // a promise for a control that has to reach the authority; both
      // answer on the same socket, once.
      try {
        Promise.resolve(this.handleRequest(JSON.parse(buffer.slice(0, newline)))).then(answer, invalid);
      } catch (error) {
        invalid(error);
      }
    });
    socket.on("end", () => {
      if (!answered && buffer.trim()) {
        try {
          Promise.resolve(this.handleRequest(JSON.parse(buffer))).then(answer, invalid);
        } catch (error) {
          invalid(error);
        }
      }
    });
    socket.on("error", (error) => this.logger.warn(`event socket client error: ${error.message}`));
  }
}

// W93: one publisher per IDENTIFIED target. `roleInstructions` already
// carries the baton binary and config, and the target identity carries
// the participant — the three facts a runtime lease needs and the same
// three every other Baton invocation here names explicitly. A target
// without an identity has no participant to report as, so it gets the
// silent publisher rather than a guess: the adapter family is never
// inferred, and neither is who a runner belongs to.
function defaultRuntimeFactory(config, target, logger) {
  if (!config.roleInstructions || !target.identity) return silentPublisher;
  return makeRuntimePublisher({
    binary: config.roleInstructions.binary,
    config: config.roleInstructions.config,
    participant: target.identity.participant,
  }, { adapter: "codex", logger,
       // R9: the owner is carried from the deployment configuration,
       // never guessed from a participant or target name.
       actionOwner: target.identity.actionOwner });
}
