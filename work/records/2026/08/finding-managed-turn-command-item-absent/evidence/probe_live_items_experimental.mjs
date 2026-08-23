// W7989 bounded live probe — EXPERIMENTAL-API OPT-IN variant (plan item 5).
// Identical to probe_live_items.mjs except capabilities.experimentalApi.
// It runs one harmless managed turn, retains only item type counts and the
// custom exec call/output pair, and prints bounded JSON evidence.

import { chmodSync, copyFileSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { spawn } from "node:child_process";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { randomUUID } from "node:crypto";
import { createInterface } from "node:readline";

const workspace = mkdtempSync(join(tmpdir(), "w7989-exp-probe-"));
const codexHome = mkdtempSync(join(tmpdir(), "w7989-exp-probe-codex-"));
copyFileSync(join(homedir(), ".codex", "auth.json"),
	join(codexHome, "auth.json"));
chmodSync(join(codexHome, "auth.json"), 0o600);
writeFileSync(join(codexHome, "config.toml"),
	'model = "gpt-5.6-sol"\nmodel_reasoning_effort = "low"\n');
const typeCounts = new Map();
const notificationCounts = new Map();
const serverRequestMethods = [];
const customItems = [];
const liveItems = [];
const completed = new Map();
let threadId = null;
let turnId = null;
let server = null;
let serverError = "";
let nextId = 1;
const pending = new Map();

function send(message) {
	server.stdin.write(`${JSON.stringify(message)}\n`);
}

function request(method, params) {
	const id = nextId++;
	return new Promise((resolve, reject) => {
		const timer = setTimeout(() => {
			pending.delete(id);
			reject(new Error(`${method} timed out`));
		}, 30_000);
		pending.set(id, { method, resolve, reject, timer });
		send({ method, id, params });
	});
}

async function startServer() {
	server = spawn("codex", ["app-server"],
		{ env: { ...process.env, CODEX_HOME: codexHome },
		  stdio: ["pipe", "pipe", "pipe"] });
	server.stderr.on("data", (chunk) => {
		serverError = bounded(serverError + chunk.toString(), 2000);
	});
	server.on("exit", (code) => {
		for (const { reject, timer } of pending.values()) {
			clearTimeout(timer);
			reject(new Error(`app-server exited ${code}; stderr=${serverError}`));
		}
		pending.clear();
	});
	const lines = createInterface({ input: server.stdout });
	lines.on("line", (line) => receive(JSON.parse(line)));
	await request("initialize", {
		clientInfo: { name: "w7989_raw_probe_experimental", title: "W7989 Raw Probe",
			version: "0.1.0" },
		capabilities: { experimentalApi: true, requestAttestation: false,
			optOutNotificationMethods: ["item/agentMessage/delta",
				"item/commandExecution/outputDelta", "item/reasoning/summaryTextDelta",
				"item/reasoning/textDelta"] },
	});
	send({ method: "initialized" });
}

function bounded(value, limit = 3000) {
	const text = typeof value === "string" ? value : JSON.stringify(value);
	return text.length > limit
		? `${text.slice(0, limit)}… (${text.length} chars)` : text;
}

function notification(method, params) {
	notificationCounts.set(method, (notificationCounts.get(method) ?? 0) + 1);
	if (method === "turn/completed" && params?.threadId && params?.turn?.id) {
		completed.set(`${params.threadId}\0${params.turn.id}`, params.turn);
	}
	// W7989 implementer addition: the operator run reported item/started 3 and
	// item/completed 3 while the STORED turn carried two item types. Something
	// is announced live and not persisted, and counts cannot say what it is.
	// Bounded exactly like everything else here: the type, the id, and for a
	// command-shaped item its command and status.
	if (method === "item/started" || method === "item/completed") {
		if (threadId !== null && params?.threadId !== threadId) return;
		if (turnId !== null && params?.turnId !== turnId) return;
		const item = params?.item ?? {};
		liveItems.push({ event: method, type: item.type ?? null,
			id: item.id ?? null, status: item.status ?? null,
			keys: Object.keys(item).slice(0, 12),
			command: item.command === undefined
				? null : bounded(item.command, 200),
			name: item.name ?? null,
			exitCode: item.exitCode ?? null });
		return;
	}
	if (method !== "rawResponseItem/completed") return;
	if (threadId !== null && params?.threadId !== threadId) return;
	if (turnId !== null && params?.turnId !== turnId) return;
	const item = params?.item ?? {};
	typeCounts.set(item.type, (typeCounts.get(item.type) ?? 0) + 1);
	if (item.type === "custom_tool_call") {
		customItems.push({ type: item.type, id: item.id ?? null,
			call_id: item.call_id ?? null, name: item.name ?? null,
			status: item.status ?? null, input: bounded(item.input) });
	} else if (item.type === "custom_tool_call_output") {
		customItems.push({ type: item.type, id: item.id ?? null,
			call_id: item.call_id ?? null, name: item.name ?? null,
			output: bounded(item.output) });
	}
}

function receive(message) {
	if (Object.hasOwn(message, "id") && !Object.hasOwn(message, "method")) {
		const waiting = pending.get(message.id);
		if (!waiting) return;
		pending.delete(message.id);
		clearTimeout(waiting.timer);
		if (message.error) {
			waiting.reject(new Error(`${waiting.method}: ${message.error.message}`));
		} else {
			waiting.resolve(message.result);
		}
		return;
	}
	if (Object.hasOwn(message, "id") && message.method) {
		serverRequestMethods.push(message.method);
		send({ id: message.id, error: { code: -32601,
			message: "W7989 bounded probe denies every interactive request" } });
		return;
	}
	if (message.method) notification(message.method, message.params);
}

async function waitForCompletion() {
	const key = `${threadId}\0${turnId}`;
	const deadline = Date.now() + 90_000;
	while (!completed.has(key)) {
		if (Date.now() > deadline) throw new Error(`turn ${turnId} timed out`);
		await new Promise((resolve) => setTimeout(resolve, 50));
	}
	return completed.get(key);
}

try {
	await startServer();
	const started = await request("thread/start", {
		cwd: workspace,
		developerInstructions: "Run exactly the one harmless shell command the user gives you. Use the available shell execution tool exactly once, wait for its result, and reply with only stdout. Do not run anything else.",
	});
	threadId = started.thread.id;
	const turn = await request("turn/start", { threadId,
		clientUserMessageId: randomUUID(),
		input: [{ type: "text",
			text: "Run exactly `date +%s%N` once and reply with only its exact stdout.",
			text_elements: [] }] });
	turnId = turn.turn.id;
	await waitForCompletion();
	const stored = await request("thread/read", { threadId,
		includeTurns: true });
	const storedTurn = (stored.thread?.turns ?? [])
		.find((entry) => entry.id === turnId);
	console.log(JSON.stringify({ threadId, turnId,
		notificationCounts: Object.fromEntries(notificationCounts),
		serverRequestMethods,
		rawResponseItemTypeCounts: Object.fromEntries(typeCounts), customItems,
		liveItems,
		storedTurnStatus: storedTurn?.status ?? null,
		storedThreadItemTypes: (storedTurn?.items ?? []).map((item) => item.type),
	}, null, 2));
} catch (error) {
	console.log(JSON.stringify({ threadId, turnId, error: error.message,
		serverError, notificationCounts: Object.fromEntries(notificationCounts),
		serverRequestMethods,
		rawResponseItemTypeCounts: Object.fromEntries(typeCounts), customItems,
		liveItems,
	}, null, 2));
	process.exitCode = 1;
} finally {
	server?.kill("SIGTERM");
	rmSync(workspace, { recursive: true, force: true });
	rmSync(codexHome, { recursive: true, force: true });
}
