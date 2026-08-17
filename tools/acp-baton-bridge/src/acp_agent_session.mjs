// ACP process/session ownership (slice A): spawn the CONFIGURED agent
// subprocess, speak JSON-RPC over its stdio through the pinned official
// SDK, negotiate capabilities BEFORE any session use, establish or load
// the one configured session, require the exact configured permission
// mode, and serialize prompt turns. Fail closed everywhere: an
// unsupported mode, missing load capability, or unexpected permission
// request is a visible failure, never a fallback — and a session is
// REUSABLE only after the complete setup succeeded (W163 R2); every
// setup failure kills and forgets the partial connection. Setup calls
// race the child's exit, spawn errors, and an explicit deadline so
// supervision can never wait forever (W163 R4).

import { spawn } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { Readable, Writable } from "node:stream";
import {
	ClientSideConnection,
	PROTOCOL_VERSION,
	ndJsonStream,
} from "@agentclientprotocol/sdk";

class PolicyViolation extends Error {}
class SessionSetupError extends Error {}
// W27: a session-SELECTION fault, distinct from a setup fault. Retrying
// cannot fix a launch that would replace somebody's continuity, so the
// bridge never folds one of these into its ordinary retry loop.
class SessionStateError extends Error {}

export function sessionStatePathFor(config) {
	return join(config.stateDir, "session.json");
}

// W27: absent, malformed and unreadable are THREE different facts, not
// one null. Only genuine absence permits a first bootstrap; anything
// already on disk is a selection somebody may still be resuming, and it
// is preserved and named rather than overwritten or guessed at.
export function readSessionSelection(path) {
	let text;
	try {
		text = readFileSync(path, "utf8");
	} catch (error) {
		if (error.code === "ENOENT") return { state: "absent" };
		return { state: "unreadable", reason: error.message };
	}
	let parsed;
	try {
		parsed = JSON.parse(text);
	} catch (error) {
		return { state: "malformed", reason: error.message };
	}
	const sessionId = parsed?.sessionId;
	if (typeof sessionId !== "string" || !sessionId) {
		return { state: "malformed",
		         reason: "no non-empty 'sessionId' string" };
	}
	return { state: "present", sessionId };
}

// ONE selection decision per bridge run, taken at STARTUP — before the
// Baton wait and before any agent spawns — so a misconfigured launch is
// an immediate nonzero result rather than a deferred retry loop that
// looks healthy while idle.
//
// `new` MAKES a continuity context, so it is correct only when none has
// been selected yet; `--once` independently controls bridge lifetime and
// never licenses a second creation. `load` RESUMES one, so it resolves
// and validates that id here and RETAINS it for the whole run (W27 R2).
// After this returns, no rebuild consults the file again: a run holds
// exactly one continuity context, and an external edit mid-run cannot
// steer a replacement process onto a different session. Rotation stays
// deliberately absent — create first with `new`, then resume with
// `load`.
export function preflightSessionSelection(config, runSelection) {
	const path = sessionStatePathFor(config);
	const selection = readSessionSelection(path);
	if (config.session.mode === "new") {
		if (selection.state === "absent") return;
		if (selection.state === "present") {
			throw new SessionStateError(
				`session.mode=new but ${path} already selects session `
				+ `${selection.sessionId}; refusing rather than replacing `
				+ `it — resume that session with a 'load' configuration`);
		}
		throw new SessionStateError(
			`session.mode=new but ${path} already exists and is not a `
			+ `usable session selection (${selection.reason}); refusing `
			+ `rather than replacing it — the file is preserved for `
			+ `inspection`);
	}
	if (selection.state === "absent") {
		throw new SessionStateError(
			`session.mode=load but no persisted session exists in ${path}; `
			+ `run a 'new' bootstrap deliberately first`);
	}
	// Existing-but-unusable is NOT absence, and must never be answered
	// with "bootstrap a new one" — that advice would discard a selection
	// whose id may still be recoverable from the file itself.
	if (selection.state !== "present") {
		throw new SessionStateError(
			`session.mode=load but ${path} is not a usable session `
			+ `selection (${selection.reason}); refusing — the file is `
			+ `preserved, repair or remove it deliberately`);
	}
	if (runSelection) runSelection.sessionId = selection.sessionId;
}

export class AcpAgentSession {
	constructor(config, { logger = console, onUpdate, runSelection } = {}) {
		this.config = config;
		this.logger = logger;
		// W27 R1: RUN-scoped, deliberately shared across every session
		// object one bridge builds. Once this run has published its
		// first selection it RETAINS that id: an agent PROCESS dying is
		// not the ACP session dying, so a replacement process resumes
		// the same session rather than creating — and silently rotating
		// to — another one.
		this.runSelection = runSelection ?? { published: false,
		                                      sessionId: null };
		// The foreground surface: streamed activity and genuine agent
		// elicitation/questions belong to the operator — never command
		// approvals (the ruled bypass boundary).
		this.onUpdate = onUpdate ?? ((line) => logger.info(line));
		this.child = null;
		this.connection = null;
		this.sessionId = null;
		this.turn = Promise.resolve();     // busy serialization
		this.exited = null;
		this.spawnError = null;
		this.policyFailure = null;
		// R2: published as reusable ONLY after initialize, session
		// new/load, and exact mode enforcement ALL succeed.
		this.ready = false;
	}

	alive() {
		return this.ready && this.child !== null
			&& this.child.exitCode === null && !this.spawnError;
	}

	sessionStatePath() {
		return sessionStatePathFor(this.config);
	}

	// The bridge persists ONLY its own session selection — never agent
	// history, never Baton authority state.
	sessionSelection() {
		return readSessionSelection(this.sessionStatePath());
	}

	persistedSessionId() {
		const selection = this.sessionSelection();
		return selection.state === "present" ? selection.sessionId : null;
	}

	// W27: publication is CREATE-ONLY and happens exactly ONCE per run.
	// The startup preflight closes the common case, but it cannot close
	// the window between itself and this write, so the filesystem
	// settles the race: whoever creates the file wins, and the loser
	// abandons its own fresh session rather than replacing the winner's
	// byte-for-byte. W27 R1: there is no second write. The selection is
	// immutable for the life of the run, and a replacement agent
	// process resumes the retained id instead of rewriting this file.
	persistSessionId(sessionId) {
		mkdirSync(this.config.stateDir, { recursive: true });
		try {
			writeFileSync(this.sessionStatePath(),
			              `${JSON.stringify({ sessionId }, null, 2)}\n`,
			              { flag: "wx" });
		} catch (error) {
			if (error.code !== "EEXIST") throw error;
			throw new SessionStateError(
				`another bridge published ${this.sessionStatePath()} while `
				+ `this bootstrap was creating session ${sessionId}; the `
				+ `existing selection is preserved and this session is `
				+ `abandoned — resume the winner with a 'load' `
				+ `configuration`);
		}
		this.runSelection.published = true;
		this.runSelection.sessionId = sessionId;
	}

	// R4: every setup call races the subprocess's death, a spawn
	// error, and the configured deadline — supervision never waits on
	// an unresponsive protocol call.
	supervised(promise, what, deadlineMs) {
		let timer;
		const guard = new Promise((_resolve, reject) => {
			timer = setTimeout(() => reject(new SessionSetupError(
				`${what} did not complete within ${deadlineMs}ms; `
				+ `refusing an unresponsive agent`)), deadlineMs);
			this.exited?.then((exit) => reject(new SessionSetupError(
				`the agent exited (${JSON.stringify(exit)}) before `
				+ `${what} completed`)));
		});
		return Promise.race([promise, guard])
			.finally(() => clearTimeout(timer));
	}

	async start() {
		try {
			return await this.setup();
		} catch (error) {
			// R2: a failed setup NEVER leaves a partial connection for
			// reuse — kill and forget before the caller retries.
			await this.stop();
			this.ready = false;
			throw error;
		}
	}

	async setup() {
		const { command, args, env, cwd } = this.config.agent;
		this.child = spawn(command, args, {
			cwd,
			env: { ...process.env, ...env },
			stdio: ["pipe", "pipe", "inherit"],
		});
		this.exited = new Promise((resolve) => {
			this.child.once("exit", (code, signalName) =>
				resolve({ code, signal: signalName }));
			// A missing executable never spawns and never exits: the
			// error event is part of this lifecycle boundary.
			this.child.once("error", (error) => {
				this.spawnError = error;
				resolve({ code: null, signal: null,
				          error: error.message });
			});
		});
		const stream = ndJsonStream(
			Writable.toWeb(this.child.stdin),
			Readable.toWeb(this.child.stdout));
		this.connection = new ClientSideConnection(
			() => this.clientHandler(), stream);
		const deadline = this.config.setupTimeoutMs;

		// 1. Initialize and negotiate BEFORE any session use.
		const init = await this.supervised(this.connection.initialize({
			protocolVersion: PROTOCOL_VERSION,
			clientCapabilities: {},
			clientInfo: { name: "acp-baton-bridge", version: "0.1.0" },
		}), "initialize", deadline);
		this.capabilities = init.agentCapabilities ?? {};
		// W27 R1: a run that has already published RESUMES its retained
		// session, so it needs the load capability exactly as much as a
		// configured `load` run does. Creating a replacement session is
		// never the fallback — that is the rotation this finding closes.
		const resumeExisting = this.config.session.mode === "load"
			|| this.runSelection.published;
		if (resumeExisting && !this.capabilities.loadSession) {
			throw new SessionSetupError(
				(this.config.session.mode === "load"
					? "session.mode=load is configured"
					: `this run already selected session `
						+ `${this.runSelection.sessionId} to resume`)
				+ " but the agent does not advertise the loadSession "
				+ "capability; refusing — continuity may not be assumed");
		}

		// 2. Establish exactly the configured session.
		let response;
		if (resumeExisting) {
			// W27 R2: ALWAYS the retained id — run state settled by the
			// startup preflight, never a re-read. Both entries are
			// symmetric here: a `new` run retains what it published, a
			// `load` run retains what the preflight validated, and
			// neither lets a mid-run file change pick the session.
			const sessionId = this.runSelection.sessionId;
			response = await this.supervised(this.connection.loadSession({
				sessionId, cwd: this.config.session.cwd, mcpServers: [],
			}), "session/load", deadline);
			this.sessionId = sessionId;
		} else {
			response = await this.supervised(this.connection.newSession({
				cwd: this.config.session.cwd, mcpServers: [],
			}), "session/new", deadline);
			this.sessionId = response.sessionId;
		}

		// 3. Require the EXACT configured permission mode. No fallback,
		// no prompt-mode downgrade — fail visibly instead.
		await this.enforceMode(response?.modes ?? null);

		// R6: the session id becomes RESUMABLE state only after the
		// complete setup boundary — mode enforcement included — has
		// succeeded. A rejected setup persists nothing, and a failed
		// bootstrap never erases an earlier accepted session record.
		// W27 R1: exactly one publication per run; a resumed rebuild
		// republishes nothing.
		if (this.config.session.mode === "new" && !resumeExisting) {
			this.persistSessionId(this.sessionId);
		}
		this.ready = true;
		return this.sessionId;
	}

	async enforceMode(modes) {
		const wanted = this.config.permissionMode;
		if (!modes || !Array.isArray(modes.availableModes)) {
			throw new SessionSetupError(
				`the agent advertised no session modes; the configured `
				+ `permission mode '${wanted}' cannot be required — `
				+ `refusing`);
		}
		const available = modes.availableModes.map((mode) => mode.id);
		if (!available.includes(wanted)) {
			throw new SessionSetupError(
				`the configured permission mode '${wanted}' is not among `
				+ `the agent's available modes [${available.join(", ")}]; `
				+ `refusing rather than falling back`);
		}
		if (modes.currentModeId !== wanted) {
			await this.supervised(this.connection.setSessionMode({
				sessionId: this.sessionId, modeId: wanted }),
				"session/set_mode", this.config.setupTimeoutMs);
		}
		this.modeActive = wanted;
	}

	clientHandler() {
		const session = this;
		return {
			// The ruled boundary: with the configured bypass mode
			// active, an ACP permission request is a policy/protocol
			// FAILURE — cancelled and reported, never silently allowed
			// and never auto-approved.
			requestPermission(params) {
				const title = params?.toolCall?.title ?? "unnamed tool call";
				session.policyFailure = new PolicyViolation(
					`unexpected ACP permission request ('${title}') while `
					+ `permission mode '${session.config.permissionMode}' `
					+ `is active — cancelled and reported as a `
					+ `policy/protocol failure`);
				session.logger.warn(session.policyFailure.message);
				return { outcome: { outcome: "cancelled" } };
			},
			sessionUpdate(params) {
				const update = params?.update ?? {};
				if (update.sessionUpdate === "agent_message_chunk"
						&& update.content?.type === "text") {
					session.onUpdate(update.content.text);
				} else if (update.sessionUpdate === "tool_call"
						|| update.sessionUpdate === "tool_call_update") {
					session.onUpdate(
						`[${update.sessionUpdate}] ${update.title ?? ""} `
						+ `${update.status ?? ""}`.trim());
				} else if (update.sessionUpdate) {
					session.onUpdate(`[${update.sessionUpdate}]`);
				}
			},
		};
	}

	// Busy sessions serialize ordinary Baton wakes (acceptance 5): one
	// turn at a time, strictly in arrival order; a queued wake is never
	// dropped and never steers the running turn. A turn has no
	// arbitrary work deadline, but it races the agent's DEATH so a
	// killed or crashed subprocess rejects instead of hanging (R4).
	promptText(text) {
		const run = this.turn.then(async () => {
			this.policyFailure = null;
			const turnDone = this.connection.prompt({
				sessionId: this.sessionId,
				prompt: [{ type: "text", text }],
			});
			const death = this.exited.then((exit) => {
				throw new SessionSetupError(
					`the agent exited (${JSON.stringify(exit)}) `
					+ `mid-turn`);
			});
			const response = await Promise.race([turnDone, death]);
			if (this.policyFailure) throw this.policyFailure;
			return response;
		});
		// The queue survives individual failures.
		this.turn = run.then(() => undefined, () => undefined);
		return run;
	}

	async stop() {
		this.ready = false;
		if (this.child && this.child.exitCode === null
				&& !this.spawnError) {
			this.child.kill("SIGTERM");
			const grace = new Promise((resolve) =>
				setTimeout(resolve, 500));
			const exit = await Promise.race([this.exited, grace]);
			if (exit === undefined && this.child.exitCode === null) {
				this.child.kill("SIGKILL");
				await this.exited;
			}
		}
	}
}

export { PolicyViolation, SessionSetupError, SessionStateError };
