#!/usr/bin/env node
// The fake ACP agent (slice A harness): a real subprocess speaking the
// SAME pinned SDK over its own stdio, with every behavior the
// acceptance needs selected by environment variables:
//
//   FAKE_ACP_LOG           append-only JSONL evidence file (required)
//   FAKE_ACP_NO_BYPASS=1   advertise modes WITHOUT bypassPermissions
//   FAKE_ACP_NO_MODES=1    advertise no modes at all
//   FAKE_ACP_NO_LOAD=1     do not advertise the loadSession capability
//   FAKE_ACP_PERMISSION=1  request permission during each prompt turn
//   FAKE_ACP_SLOW_MS=n     hold each prompt turn open n milliseconds
//   FAKE_ACP_MALFORMED=1   emit one garbage line before initialize
//   FAKE_ACP_EXIT_ON_PROMPT=1  exit(7) when the first prompt arrives
//   FAKE_ACP_MUTE=1        never answer initialize (hang forever)
//   FAKE_ACP_NEVER_FINISH=1    prompt turns never return
//   FAKE_ACP_CHATTY_MS=n       while hung, emit a session update every
//                              n ms — the "infinite but talkative tool"
//                              an activity-reset watchdog would never
//                              end (W28681)
//   FAKE_ACP_LEAVE_DESCENDANT=PATH
//                              during the turn, start a DETACHED child
//                              in its own session (`setsid`) that
//                              outlives this process, and write its pid
//                              to PATH. This is the exact shape the
//                              incident found: a tool child that a
//                              process-group signal cannot reach
//   FAKE_ACP_TRY_FORBIDDEN=1   attempt the tool "forbidden_tool" in
//                              each turn, gated by the deployment
//                              policy file at FAKE_ACP_POLICY; a
//                              successful (undenied) attempt writes
//                              FAKE_ACP_SIDE_EFFECT — the harness's
//                              proof that a denial had NO side effect

import { appendFileSync } from "node:fs";
import { randomUUID } from "node:crypto";
import { Readable, Writable } from "node:stream";
import {
	AgentSideConnection,
	PROTOCOL_VERSION,
	ndJsonStream,
} from "@agentclientprotocol/sdk";

const logPath = process.env.FAKE_ACP_LOG;
if (!logPath) {
	process.stderr.write("fake_acp_agent: FAKE_ACP_LOG is required\n");
	process.exit(2);
}

function log(record) {
	appendFileSync(logPath,
		`${JSON.stringify({ at: Date.now(), ...record })}\n`);
}

// W14828: WHAT THIS PROCESS ACTUALLY INHERITED, recorded at startup.
//
// The incident was a launcher contract that existed in the rendered runtime
// context and reached neither the spawned environment nor the prompt, so the
// model went looking and found a stale persistent file. A test that read the
// bridge's own config object would prove the config object; only the real
// child can say what the real spawn delivered, which is why this record is
// taken here rather than asserted there.
log({
	event: "launcher/env",
	BATON_BIN: process.env.BATON_BIN ?? null,
	BATON_CONFIG: process.env.BATON_CONFIG ?? null,
	BATON_PARTICIPANT: process.env.BATON_PARTICIPANT ?? null,
	BATON_ROLE: process.env.BATON_ROLE ?? null,
});

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function modes() {
	if (process.env.FAKE_ACP_NO_MODES) return null;
	const available = [{ id: "default", name: "Default" }];
	if (!process.env.FAKE_ACP_NO_BYPASS) {
		available.push({ id: "bypassPermissions", name: "Bypass Permissions" });
	}
	return { currentModeId: "default", availableModes: available };
}

class FakeAgent {
	constructor(connection) {
		this.connection = connection;
		this.currentMode = "default";
	}

	async initialize(params) {
		if (process.env.FAKE_ACP_MUTE) {
			log({ event: "initialize/muted" });
			return new Promise(() => {});      // never answers
		}
		log({ event: "initialize", protocolVersion: params.protocolVersion });
		return {
			protocolVersion: PROTOCOL_VERSION,
			agentCapabilities: {
				loadSession: !process.env.FAKE_ACP_NO_LOAD,
			},
		};
	}

	async newSession(params) {
		const sessionId = randomUUID();
		log({ event: "session/new", sessionId, cwd: params.cwd });
		return { sessionId, modes: modes() };
	}

	async loadSession(params) {
		log({ event: "session/load", sessionId: params.sessionId,
		      cwd: params.cwd });
		return { modes: modes() };
	}

	async setSessionMode(params) {
		this.currentMode = params.modeId;
		log({ event: "session/set_mode", sessionId: params.sessionId,
		      modeId: params.modeId });
		return {};
	}

	async authenticate() {
		return {};
	}

	async prompt(params) {
		const text = params.prompt.map((block) =>
			block.type === "text" ? block.text : `[${block.type}]`).join("");
		log({ event: "prompt/start", sessionId: params.sessionId, text,
		      mode: this.currentMode });
		if (process.env.FAKE_ACP_EXIT_ON_PROMPT) {
			log({ event: "exit" });
			process.exit(7);
		}
		await this.connection.sessionUpdate({
			sessionId: params.sessionId,
			update: {
				sessionUpdate: "agent_message_chunk",
				content: { type: "text", text: `echo: ${text.slice(0, 40)}` },
			},
		});
		if (process.env.FAKE_ACP_LEAVE_DESCENDANT) {
			// W28681: a tool child in ITS OWN session, exactly as the
			// four polling shells in the incident were. `detached` makes
			// this process a session and process-group leader, so a
			// signal to this agent's group cannot reach it — only an
			// outer domain can.
			const { spawn: spawnChild } = await import("node:child_process");
			const { writeFileSync: write } = await import("node:fs");
			const child = spawnChild(process.execPath,
				["-e", "setInterval(() => {}, 1000)"],
				{ detached: true, stdio: "ignore" });
			child.unref();
			write(process.env.FAKE_ACP_LEAVE_DESCENDANT, `${child.pid}\n`);
			log({ event: "tool/descendant", pid: child.pid });
		}
		if (process.env.FAKE_ACP_NEVER_FINISH) {
			log({ event: "prompt/hung" });
			if (process.env.FAKE_ACP_CHATTY_MS) {
				// W28681: updates FOREVER, and they have to be VALID ones.
				//
				// Review [P1]: this update omitted `toolCallId`, which is the
				// one member `ToolCallUpdate` requires. The SDK rejected every
				// one with `Invalid params`, so nothing ever reached the
				// bridge's handler — the case reached its deadline over a
				// SILENT agent and proved nothing about whether real streamed
				// activity extends it, which is the only thing it was for.
				const every = Number(process.env.FAKE_ACP_CHATTY_MS);
				let beats = 0;
				const beat = setInterval(() => {
					beats += 1;
					this.connection.sessionUpdate({
						sessionId: params.sessionId,
						update: { sessionUpdate: "tool_call_update",
						          toolCallId: "w28681-chatty-tool",
						          title: `still going (${beats})`,
						          status: "in_progress" },
					}).then(() => log({ event: "tool/update", beat: beats }),
					        (error) => log({ event: "tool/update-refused",
					                         why: String(error?.message
					                                     ?? error) }));
				}, every);
				beat.unref?.();
			}
			return new Promise(() => {});      // the turn never ends
		}
		if (process.env.FAKE_ACP_TRY_FORBIDDEN) {
			// Deployment-owned hard denial, modeled agent-side exactly
			// as ruled: the policy resource decides; the bridge never
			// parses commands. A denial has NO side effect and NO
			// permission prompt; an unreadable policy FAILS CLOSED.
			const { readFileSync: read } = await import("node:fs");
			const { appendFileSync: append } = await import("node:fs");
			let denied = null;
			try {
				denied = JSON.parse(read(process.env.FAKE_ACP_POLICY,
				                         "utf8")).denied ?? [];
			} catch {
				log({ event: "hook/failure",
				      detail: "policy unreadable; failing closed" });
				await this.connection.sessionUpdate({
					sessionId: params.sessionId,
					update: { sessionUpdate: "tool_call",
					          toolCallId: "call_f", title: "forbidden_tool",
					          kind: "execute", status: "failed" } });
				return { stopReason: "refusal" };
			}
			if (denied.includes("forbidden_tool")) {
				log({ event: "tool/denied", tool: "forbidden_tool" });
				await this.connection.sessionUpdate({
					sessionId: params.sessionId,
					update: { sessionUpdate: "tool_call",
					          toolCallId: "call_f", title: "forbidden_tool",
					          kind: "execute", status: "failed" } });
			} else {
				append(process.env.FAKE_ACP_SIDE_EFFECT,
				       "forbidden side effect happened\n");
				log({ event: "tool/ran", tool: "forbidden_tool" });
			}
		}
		if (process.env.FAKE_ACP_PERMISSION) {
			const response = await this.connection.requestPermission({
				sessionId: params.sessionId,
				toolCall: { toolCallId: "call_1", title: "forbidden thing" },
				options: [
					{ optionId: "allow", name: "Allow", kind: "allow_once" },
					{ optionId: "deny", name: "Deny", kind: "reject_once" },
				],
			});
			log({ event: "permission/outcome",
			      outcome: response.outcome });
		}
		const slow = Number(process.env.FAKE_ACP_SLOW_MS ?? 0);
		if (slow > 0) await sleep(slow);
		log({ event: "prompt/end", sessionId: params.sessionId, text });
		return { stopReason: "end_turn" };
	}

	async cancel() {}
}

if (process.env.FAKE_ACP_MALFORMED) {
	process.stdout.write("this line is not JSON-RPC\n");
}

const stream = ndJsonStream(
	Writable.toWeb(process.stdout),
	Readable.toWeb(process.stdin));
new AgentSideConnection((connection) => new FakeAgent(connection), stream);

// R1: the agent owns its lifetime explicitly. A JSON-RPC server whose
// only handle is a wrapped stdin must not depend on any particular
// Node version's event-loop accounting: hold a keepalive and exit
// deliberately when the client closes the channel.
const keepalive = setInterval(() => {}, 1 << 30);
process.stdin.once("end", () => { clearInterval(keepalive); process.exit(0); });
process.stdin.once("close", () => { clearInterval(keepalive); process.exit(0); });
