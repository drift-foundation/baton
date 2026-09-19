// W195314: local operator intent belongs to the session owner, never to a
// second ACP connection or readiness consumer. This journal is not Work state.
import { randomUUID } from "node:crypto";
import { chmodSync, closeSync, fsyncSync, mkdirSync, openSync, readFileSync,
         renameSync, writeFileSync } from "node:fs";
import { createConnection, createServer } from "node:net";
import { join } from "node:path";

export const controlPath = (config) => join(config.stateDir, "operator.sock");
const LIMIT = 65536;
const targetKeys = ["bridgeId", "sessionId", "turnId"];
const sameTarget = (a, b) => targetKeys.every((key) =>
	typeof a?.[key] === "string" && a[key] === b?.[key]);
const nonblank = (value) => typeof value === "string" && value.trim().length > 0;

export class OperatorControl {
	constructor(config) {
		this.config = config;
		this.bridgeId = randomUUID();
		this.path = join(config.stateDir, "operator.json");
		this.record = null;
		this.active = null;
		this.pending = null;
		this.sockets = new Set();
	}

	restore() {
		try {
			this.record = JSON.parse(readFileSync(this.path, "utf8"));
			if (this.record?.version !== 1
					|| this.record.participant !== this.config.baton.participant
					|| typeof this.record.hold !== "boolean"
					|| !targetKeys.every((key) => nonblank(this.record[key]))
					|| typeof this.record.domainExited !== "boolean") {
				throw new Error("invalid operator journal");
			}
			// A queued continuation was never admitted. An executing one has
			// an unknown process outcome after restart. Neither is replayed.
			if (this.record.hold) {
				this.record.status = this.record.domainExited
					? "held-after-restart" : "unsettled-after-restart";
				this.save(this.record);
			}
		} catch (error) {
			if (error.code !== "ENOENT") throw error;
		}
	}

	async start() {
		mkdirSync(this.config.stateDir, { recursive: true, mode: 0o700 });
		this.server = createServer((socket) => {
			this.sockets.add(socket);
			socket.once("close", () => this.sockets.delete(socket));
			socket.on("error", () => {});
			socket.setTimeout(5000, () => socket.destroy());
			let input = "";
			let answered = false;
			socket.on("data", (chunk) => {
				if (answered) return;
				input += chunk.toString("utf8");
				if (Buffer.byteLength(input) > LIMIT) return socket.destroy();
				if (!input.includes("\n")) return;
				answered = true;
				try {
					const result = this.handle(JSON.parse(input.slice(0, input.indexOf("\n"))));
					socket.end(`${JSON.stringify({ ok: true, ...result })}\n`);
				} catch (error) {
					socket.end(`${JSON.stringify({ ok: false, error: error.message })}\n`);
				}
			});
		});
		// Never unlink an occupied/stale path to acquire another owner's lane.
		await new Promise((resolve, reject) => {
			this.server.once("error", reject);
			this.server.listen(controlPath(this.config), resolve);
		});
		try {
			chmodSync(controlPath(this.config), 0o600);
			this.restore();
		} catch (error) {
			await this.close();
			throw error;
		}
	}

	save(record) {
		// Synchronous durable publication is before notification/admission.
		// Keep the in-process fence too if disk publication fails.
		this.record = structuredClone(record);
		const temp = `${this.path}.${this.bridgeId}.tmp`;
		const fd = openSync(temp, "w", 0o600);
		try {
			writeFileSync(fd, `${JSON.stringify(this.record, null, 2)}\n`);
			fsyncSync(fd);
		} finally { closeSync(fd); }
		renameSync(temp, this.path);
		const dir = openSync(this.config.stateDir, "r");
		try { fsyncSync(dir); } finally { closeSync(dir); }
	}

	status() {
		return { participant: this.config.baton.participant,
			bridgeId: this.bridgeId, active: this.active?.view ?? null,
			hold: this.record?.hold === true, record: this.record };
	}

	handle(request) {
		if (request.participant !== this.config.baton.participant) {
			throw new Error("participant mismatch");
		}
		if (request.command === "status") return this.status();
		if (request.command === "cancel") {
			if (sameTarget(request, this.record) && this.record.hold
					&& (!this.active || this.active.cancelRequested)) return this.status();
			const active = this.active;
			if (!active) throw new Error("idle: no active prompt to cancel");
			if (!sameTarget(request, active.view)) throw new Error("stale turn/session/incarnation target");
			if (active.view.phase !== "prompting") throw new Error("prompt already ended; process settlement is in progress");
			this.save({ version: 1, participant: this.config.baton.participant,
				...active.view, authority: active.authority, action: active.action,
				hold: true, status: "cancel-requested", domainExited: false,
				requestedAt: new Date().toISOString() });
			active.cancelRequested = true;
			active.cancel();
			return this.status();
		}
		if (request.command !== "continue") throw new Error("unknown operator command");
		for (const key of ["requestId", "spec", "changes"]) {
			if (!nonblank(request[key]) || request[key].length > 16000) throw new Error(`${key} must be nonblank and bounded`);
		}
		const continuation = { requestId: request.requestId, spec: request.spec, changes: request.changes,
			target: Object.fromEntries(targetKeys.map((key) => [key, request[key]])) };
		if (this.record?.continuation?.requestId === request.requestId) {
			if (JSON.stringify(this.record.continuation) !== JSON.stringify(continuation)) throw new Error("requestId reused with different target or instructions");
			return this.status();
		}
		if (!sameTarget(request, this.record)) throw new Error("stale held target");
		if (!this.record.hold || !this.record.domainExited || this.active || this.pending) {
			throw new Error("continuation requires an exited domain and an idle held lane");
		}
		this.save({ ...this.record, status: "continuation-queued", continuation });
		this.pending = continuation;
		return this.status();
	}

	// This uses the canonical envelope, independently of offer suppression:
	// a held Work's previous transport acknowledgement cannot eat continuation.
	select(envelope, ordinary) {
		if (!this.record?.hold) return ordinary;
		if (!this.pending) return [];
		const action = envelope.result.actionable.find((entry) =>
			entry.action_key === this.record.action?.action_key
			&& entry.work === this.record.action?.work
			&& entry.episode_seq === this.record.action?.episode_seq);
		if (envelope.authority_uuid !== this.record.authority || !action) {
			this.rejectContinuation("continuation-stale: canonical action or authority changed");
			return [];
		}
		return [action];
	}

	rejectContinuation(reason) {
		if (!this.pending) return;
		this.pending = null;
		this.save({ ...this.record, status: reason });
	}

	async prompt(live, text, envelope, action) {
		const continuation = this.pending;
		if (continuation && live.sessionId !== this.record.sessionId) {
			this.rejectContinuation("continuation-stale: selected ACP session changed");
			throw new Error("continuation ACP session mismatch");
		}
		const view = { bridgeId: this.bridgeId, sessionId: live.sessionId,
			turnId: randomUUID(), phase: "prompting" };
		this.active = { view, authority: envelope.authority_uuid, action,
			cancelRequested: false, continuation, ackText: "" };
		if (continuation) {
			this.pending = null;
			this.save({ ...this.record, ...view, status: "continuing",
				domainExited: false, acknowledged: false });
			text += `\n\n[BATON OPERATOR CONTINUATION]\nThe previous turn was interrupted. Do not resume superseded instructions.\nRead this revised spec before further implementation: ${continuation.spec}\nRequired changes: ${continuation.changes}\nFirst acknowledge the revised spec and summarize what changed in your own words. Start a line with this exact marker, followed on the same line by your change summary: ${this.ackMarker()}\nRe-read canonical Work detail and succeed at the standalone claim required by repository policy before execution, including when the claim is already held. If refused, stop execution and report the exact blocker through the authorized handback; never bypass dispatch draining or current canonical ownership. Preserve partial files and verify external effects before repeating any operation.\n`;
		}
		const active = this.active;
		let timer;
		let rejectCancel;
		const cancelled = new Promise((_resolve, reject) => { rejectCancel = reject; });
		active.cancel = () => {
			timer = setTimeout(() => rejectCancel(new Error("operator cancellation response timed out")), this.config.setupTimeoutMs);
			Promise.resolve().then(() => live.cancel()).catch(() =>
				rejectCancel(new Error("operator cancellation notification failed")));
		};
		try {
			const response = await Promise.race([live.promptText(text), cancelled]);
			active.stopReason = response?.stopReason ?? "unknown";
			return response;
		} catch (error) {
			active.failed = true;
			active.error = active.cancelRequested ? error.message : "continuation or prompt failed";
			throw error;
		} finally {
			clearTimeout(timer);
			active.view.phase = "settling";
		}
	}

	ackMarker() {
		return `[BATON SPEC ACK ${this.active?.continuation?.requestId}]`;
	}

	observe(text) {
		if (this.active?.continuation && this.active.ackText.length < LIMIT) {
			this.active.ackText += text;
		}
	}

	finish({ domainExited, settlement = "unknown" }) {
		const active = this.active;
		if (!active) return false;
		if (active.cancelRequested || active.continuation || this.record?.hold) {
			const acknowledgement = active.continuation && active.ackText.split("\n")
				.find((line) => line.startsWith(`${this.ackMarker()} `)
					&& line.slice(this.ackMarker().length).trim().length > 0);
			const acknowledged = Boolean(acknowledgement);
			const resumed = active.continuation && !active.cancelRequested
				&& !active.failed && active.stopReason === "end_turn"
				&& domainExited && settlement !== "stranded" && acknowledged;
			this.save({ ...this.record, ...active.view, hold: !resumed,
				status: !domainExited ? "domain-unsettled"
					: resumed ? "continued" : "held",
				domainExited, settlement, acknowledged,
				acknowledgement: acknowledgement ? acknowledgement.slice(0, 4096) : null,
				stopReason: active.stopReason ?? "unknown",
				error: active.error ?? null });
		}
		this.active = null;
		return this.record?.hold === true;
	}

	async close() {
		for (const socket of this.sockets) socket.destroy();
		if (this.server?.listening) await new Promise((resolve) => this.server.close(resolve));
	}
}

export async function requestControl(config, request) {
	return await new Promise((resolve, reject) => {
		const socket = createConnection(controlPath(config));
		let text = "";
		socket.setTimeout(5000, () => socket.destroy(new Error("operator control timed out")));
		socket.on("error", reject);
		socket.on("connect", () => socket.write(`${JSON.stringify({ ...request, participant: config.baton.participant })}\n`));
		socket.on("data", (chunk) => {
			text += chunk.toString("utf8");
			if (Buffer.byteLength(text) > LIMIT * 2) socket.destroy(new Error("oversized control response"));
		});
		socket.on("end", () => {
			try {
				const result = JSON.parse(text);
				if (!result.ok) throw new Error(result.error);
				resolve(result);
			} catch (error) { reject(error); }
		});
	});
}
