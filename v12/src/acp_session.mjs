// One ACP session against one isolated container. Structure copied from
// v11's `tools/acp-baton-bridge/src/acp_agent_session.mjs` at `8835cd5`
// (see PROVENANCE.md): negotiate capabilities BEFORE any session use,
// require the EXACT configured permission mode with no fallback, treat
// an unexpected permission request as a policy failure rather than
// silently allowing it, and race every setup call against the child's
// death and an explicit deadline.
//
// What is different here, and deliberately: the agent subprocess is
// `docker run -i`, and there is no persisted session selection. Every
// prototype attempt is a fresh single-use session — v11's W27 continuity
// machinery answers a question this proof does not ask.

import { Readable, Writable } from "node:stream";
import { ClientSideConnection, PROTOCOL_VERSION, ndJsonStream }
	from "@agentclientprotocol/sdk";
import { spawnContainer } from "./container.mjs";

class PolicyViolation extends Error {}
class SessionSetupError extends Error {}
// A turn that ran out of time, distinct from one that failed: the
// container is presumed ALIVE and must be proven gone.
class TurnTimeout extends Error {}

export class ContainerAcpSession {
	constructor(spec, { permissionMode, setupTimeoutMs = 120000,
	                    promptTimeoutMs, onUpdate } = {}) {
		this.spec = spec;
		this.permissionMode = permissionMode;
		this.setupTimeoutMs = setupTimeoutMs;
		// W76 review round 2: a MANAGER-owned deadline on the turn
		// itself, which `setupTimeoutMs` never was. Setup supervision
		// covers initialize/session/mode and stops there; a live but
		// silent agent inside a prompt kept this promise pending
		// forever, and with it the `finally`, the fence, compensation
		// and the return — so the canonical Handler was held
		// indefinitely by a turn nobody was watching.
		if (!Number.isSafeInteger(promptTimeoutMs) || promptTimeoutMs < 1) {
			throw new SessionSetupError(
				"a container ACP session needs an explicit positive "
				+ "promptTimeoutMs; an unsupervised turn can hold a claim "
				+ "for as long as the agent stays silent");
		}
		this.promptTimeoutMs = promptTimeoutMs;
		this.onUpdate = onUpdate ?? (() => {});
		this.child = null;
		this.connection = null;
		this.sessionId = null;
		this.exited = null;
		this.spawnError = null;
		this.policyFailure = null;
		this.stderrChunks = [];
		this.argv = null;
	}

	supervised(promise, what, deadlineMs) {
		let timer;
		const guard = new Promise((_resolve, reject) => {
			timer = setTimeout(() => reject(new SessionSetupError(
				`${what} did not complete within ${deadlineMs}ms; refusing an `
				+ `unresponsive agent`)), deadlineMs);
			this.exited?.then((exit) => reject(new SessionSetupError(
				`the worker container exited (${JSON.stringify(exit)}) before `
				+ `${what} completed${this.stderrTail()}`)));
		});
		return Promise.race([promise, guard]).finally(() => clearTimeout(timer));
	}

	stderrTail() {
		const text = this.stderrChunks.join("").trim();
		return text ? `; container stderr: ${text.slice(-600)}` : "";
	}

	async start() {
		try { return await this.setup(); }
		catch (error) { await this.stop(); throw error; }
	}

	async setup() {
		const spawned = spawnContainer(this.spec);
		this.child = spawned.child;
		this.argv = spawned.argv;
		this.stderrChunks = spawned.stderrChunks;
		this.exited = new Promise((resolve) => {
			this.child.once("exit", (code, signal) => resolve({ code, signal }));
			this.child.once("error", (error) => {
				this.spawnError = error;
				resolve({ code: null, signal: null, error: error.message });
			});
		});
		const stream = ndJsonStream(Writable.toWeb(this.child.stdin),
		                            Readable.toWeb(this.child.stdout));
		this.connection = new ClientSideConnection(() => this.clientHandler(), stream);

		const init = await this.supervised(this.connection.initialize({
			protocolVersion: PROTOCOL_VERSION,
			clientCapabilities: {},
			clientInfo: { name: "baton-v12-poc", version: "0-spike" },
		}), "initialize", this.setupTimeoutMs);
		this.capabilities = init.agentCapabilities ?? {};

		const session = await this.supervised(this.connection.newSession({
			cwd: this.spec.workdir, mcpServers: [],
		}), "session/new", this.setupTimeoutMs);
		this.sessionId = session.sessionId;
		await this.enforceMode(session?.modes ?? null);
		return this.sessionId;
	}

	// No fallback and no downgrade. If the exact mode this attempt was
	// configured for is unavailable, the attempt fails visibly — a
	// worker running under a permission posture nobody chose is worse
	// than a worker that did not run.
	async enforceMode(modes) {
		const wanted = this.permissionMode;
		if (!modes || !Array.isArray(modes.availableModes)) {
			throw new SessionSetupError(
				`the agent advertised no session modes; the required permission `
				+ `mode '${wanted}' cannot be enforced — refusing`);
		}
		const available = modes.availableModes.map((mode) => mode.id);
		if (!available.includes(wanted)) {
			throw new SessionSetupError(
				`the required permission mode '${wanted}' is not among the agent's `
				+ `available modes [${available.join(", ")}]; refusing rather than `
				+ `falling back`);
		}
		if (modes.currentModeId !== wanted) {
			await this.supervised(this.connection.setSessionMode({
				sessionId: this.sessionId, modeId: wanted,
			}), "session/set_mode", this.setupTimeoutMs);
		}
		this.modeActive = wanted;
		this.availableModes = available;
	}

	clientHandler() {
		const session = this;
		return {
			requestPermission(params) {
				const title = params?.toolCall?.title ?? "unnamed tool call";
				session.policyFailure = new PolicyViolation(
					`unexpected ACP permission request ('${title}') while permission `
					+ `mode '${session.permissionMode}' is active — cancelled and `
					+ `reported as a policy failure`);
				return { outcome: { outcome: "cancelled" } };
			},
			sessionUpdate(params) {
				const update = params?.update ?? {};
				const kind = update.sessionUpdate;
				if (kind === "agent_message_chunk" && update.content?.type === "text") {
					session.onUpdate({ channel: "message", text: update.content.text });
				} else if (kind === "agent_thought_chunk") {
					session.onUpdate({ channel: "thought", text: "" });
				} else if (kind === "tool_call" || kind === "tool_call_update") {
					session.onUpdate({ channel: "tool",
						text: `${kind} ${update.title ?? ""} ${update.status ?? ""}`.trim() });
				} else if (kind) {
					session.onUpdate({ channel: "meta", text: kind });
				}
			},
		};
	}

	// The turn races three things: its own completion, the container's
	// death, and the manager's deadline. `TurnTimeout` is its own type
	// because the caller must be able to tell "the agent went quiet"
	// apart from "the agent failed" — the first one leaves a container
	// that is still alive and has to be killed and PROVEN gone before
	// anything downstream is allowed to assume the Job is free.
	async prompt(text) {
		this.policyFailure = null;
		const turn = this.connection.prompt({
			sessionId: this.sessionId, prompt: [{ type: "text", text }],
		});
		const death = this.exited.then((exit) => {
			throw new SessionSetupError(
				`the worker container exited (${JSON.stringify(exit)}) mid-turn`
				+ this.stderrTail());
		});
		let timer;
		const deadline = new Promise((_resolve, reject) => {
			timer = setTimeout(() => reject(new TurnTimeout(
				`the agent turn in ${this.spec.name} produced no result within `
				+ `${this.promptTimeoutMs}ms; ending it rather than holding the `
				+ `claim on a silent agent`)), this.promptTimeoutMs);
			timer.unref?.();
		});
		let response;
		try {
			response = await Promise.race([turn, death, deadline]);
		} finally {
			clearTimeout(timer);
		}
		if (this.policyFailure) throw this.policyFailure;
		return response;
	}

	// Closing stdin is how the adapter is told the session is over; the
	// caller then proves quiescence through `docker inspect` rather than
	// assuming this worked.
	async stop() {
		try { this.child?.stdin?.end(); } catch { /* already closed */ }
		if (this.child && this.child.exitCode === null && !this.spawnError) {
			const grace = new Promise((resolve) => setTimeout(resolve, 3000));
			const exit = await Promise.race([this.exited, grace]);
			if (exit === undefined) this.child.kill("SIGKILL");
		}
	}
}

export { PolicyViolation, SessionSetupError, TurnTimeout };
