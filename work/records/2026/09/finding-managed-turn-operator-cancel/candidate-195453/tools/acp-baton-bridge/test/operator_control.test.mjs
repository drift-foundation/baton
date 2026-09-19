import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { OperatorControl, controlPath, requestControl } from "../src/operator_control.mjs";
import { runBridge } from "../src/acp_baton_bridge.mjs";
import { AcpAgentSession, DomainTeardownError } from "../src/acp_agent_session.mjs";
import { validateConfig } from "../src/config.mjs";

const participant = "baton.claude";
const authority = "7ba67cb8585dcfd250799fe0dc16e3fa";
const action = { kind: "work", action_key: "work:7ba67cb8-W123:1:g1",
	work: "7ba67cb8-W123", episode_seq: 1, config_generation: 1,
	local_id: "W123", title: "fixture", phase: "active", claimed: true };
const envelope = () => ({ protocol_version: 11, projection_version: "12.8",
	participant, authority_uuid: authority, snapshot_seq: 1,
	result: { actionable: [{ ...action }], timed_out: false } });
const quiet = { info() {}, warn() {} };
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
async function until(predicate) {
	const deadline = Date.now() + 5000;
	while (!predicate()) {
		assert.ok(Date.now() < deadline, "condition timed out");
		await sleep(5);
	}
}
function rig(mode = "cooperate") {
	const home = mkdtempSync(join(tmpdir(), "acp-operator-"));
	const log = join(home, "peer.jsonl");
	writeFileSync(log, "");
	const policy = join(home, "policy.json");
	writeFileSync(policy, "{}");
	const config = validateConfig({
		baton: { binary: "/unused/baton", config: "/unused/baton.json", participant, role: "impl" },
		runtime: { actionOwner: "baton.slaw" },
		agent: { command: process.execPath,
			args: [fileURLToPath(new URL("./fake_acp_agent.mjs", import.meta.url))],
			env: { FAKE_ACP_LOG: log, FAKE_ACP_OPERATOR: mode }, cwd: home },
		session: { mode: "new", cwd: home }, permissionMode: "bypassPermissions",
		policyResources: [policy], stateDir: join(home, "state"), retryMs: 5,
		setupTimeoutMs: 1000, turnTimeoutMs: 10000,
	});
	return { config, log, events: () => readFileSync(log, "utf8").trim().split("\n").filter(Boolean).map(JSON.parse) };
}
const target = (view) => Object.fromEntries(["bridgeId", "sessionId", "turnId"].map((key) => [key, view[key]]));
const request = (command, view, extra = {}) => ({ participant, command, ...target(view), ...extra });
const revised = { requestId: "revision-1", spec: "baton:work/records/fixture/FINDING.md", changes: "Use the revised deterministic fixture." };

test("operator exact targeting, repeat cancel, completion race, and retained hold", async () => {
	const { config } = rig();
	const control = new OperatorControl(config);
	await control.start();
	try {
		assert.throws(() => control.handle({ participant, command: "cancel" }), /idle/);
		let done;
		let cancels = 0;
		const prompt = control.prompt({ sessionId: "s", promptText: () => new Promise((resolve) => { done = resolve; }), cancel: () => { cancels++; } }, "original", envelope(), action);
		const active = control.status().active;
		for (const key of ["bridgeId", "sessionId", "turnId"]) {
			assert.throws(() => control.handle(request("cancel", { ...active, [key]: "stale" })), /stale/);
		}
		assert.throws(() => control.handle({ ...request("cancel", active), participant: "other.member" }), /participant/);
		const accepted = control.handle(request("cancel", active));
		assert.equal(accepted.record.status, "cancel-requested");
		assert.equal(accepted.record.domainExited, false);
		control.handle(request("cancel", active));
		await sleep(0);
		assert.equal(cancels, 1);
		done({ stopReason: "end_turn" }); // completion won the protocol race
		await prompt;
		assert.equal(control.finish({ domainExited: true, settlement: "released" }), true);
		assert.equal(control.record.stopReason, "end_turn");
		assert.equal(control.record.acknowledged, false);
		assert.deepEqual(control.select(envelope(), [action]), []);
		control.handle(request("cancel", active));
		assert.equal(cancels, 1);
	} finally { await control.close(); }
});

test("operator cancel after prompt completion cannot affect a following turn", async () => {
	const { config } = rig();
	const control = new OperatorControl(config);
	await control.start();
	try {
		await control.prompt({ sessionId: "s", promptText: async () => ({ stopReason: "end_turn" }) }, "original", envelope(), action);
		const old = control.status().active;
		assert.throws(() => control.handle(request("cancel", old)), /already ended/);
		control.finish({ domainExited: true, settlement: "released" });
		const turn = control.prompt({ sessionId: "s", promptText: async () => ({ stopReason: "end_turn" }) }, "next", envelope(), action);
		assert.throws(() => control.handle(request("cancel", old)), /stale/);
		await turn;
		control.finish({ domainExited: true });
	} finally { await control.close(); }
});

async function held(control, { domainExited = true } = {}) {
	let done;
	const turn = control.prompt({ sessionId: "s", promptText: () => new Promise((resolve) => { done = resolve; }), cancel: () => done({ stopReason: "cancelled" }) }, "old", envelope(), action);
	const active = control.status().active;
	control.handle(request("cancel", active));
	await turn;
	control.finish({ domainExited, settlement: "recoverable" });
	return active;
}

test("operator durable hold, corrupt journal, duplicate owner, and no queued restart replay", async () => {
	const { config } = rig();
	let control = new OperatorControl(config);
	await control.start();
	const active = await held(control);
	control.handle(request("continue", active, revised));
	const before = readFileSync(control.path);
	await assert.rejects(new OperatorControl(config).start(), /EADDRINUSE/);
	assert.deepEqual(readFileSync(control.path), before);
	assert.equal(statSync(controlPath(config)).mode & 0o777, 0o600);
	await control.close();
	control = new OperatorControl(config);
	await control.start();
	assert.equal(control.status().hold, true);
	assert.equal(control.pending, null);
	assert.deepEqual(control.select(envelope(), [action]), []);
	assert.equal(control.record.status, "held-after-restart");
	control.handle(request("continue", active, { ...revised, requestId: "revision-2" }));
	assert.equal(control.select(envelope(), []).length, 1);
	await control.close();
	writeFileSync(control.path, "broken");
	await assert.rejects(new OperatorControl(config).start());
	assert.equal(readFileSync(control.path, "utf8"), "broken");
});

test("operator refuses unknown domain, stale canonical action, and changed retry payload", async () => {
	const { config } = rig();
	const control = new OperatorControl(config);
	await control.start();
	try {
		const active = await held(control, { domainExited: false });
		assert.throws(() => control.handle(request("continue", active, revised)), /exited domain/);
	} finally { await control.close(); }
	const other = rig();
	const next = new OperatorControl(other.config);
	await next.start();
	try {
		const active = await held(next);
		next.handle(request("continue", active, revised));
		next.handle(request("continue", active, revised));
		assert.throws(() => next.handle(request("continue", active, { ...revised, changes: "different" })), /reused/);
		const changed = envelope();
		changed.authority_uuid = "different";
		assert.deepEqual(next.select(changed, [action]), []);
		assert.match(next.record.status, /stale/);
		assert.equal(next.pending, null);
		assert.equal(next.record.hold, true);
	} finally { await next.close(); }
});

for (const mode of ["cooperate", "ignore", "no-ack"]) {
	test(`operator real fake ACP tool cancellation and continuation: ${mode}`, { timeout: 12000 }, async () => {
		const { config, events } = rig(mode);
		const control = new OperatorControl(config);
		const controller = new AbortController();
		const domains = [];
		const transitions = [];
		const runtime = { start: async () => {}, facts: async () => {}, end: async () => {},
			state: async (state) => transitions.push(state), incident: async () => true };
		let polls = 0;
		const running = runBridge(config, { signal: controller.signal, operator: control,
			logger: quiet, runtime,
			loadInstructions: async () => ({ instructions: "Follow the accepted role." }),
			runWait: async () => { polls++; await sleep(5); return envelope(); },
			sessionFactory: (cfg, hooks) => {
				const session = new AcpAgentSession(cfg, hooks);
				domains.push(session);
				return session;
			} });
		try {
			await until(() => events().some((entry) => entry.event === "operator/tool-pending"));
			const status = await requestControl(config, { command: "status" });
			const active = status.active;
			const cancelled = await requestControl(config, request("cancel", active));
			assert.equal(cancelled.record.status, "cancel-requested");
			await until(() => control.record.domainExited);
			assert.equal(control.status().hold, true);
			assert.equal(control.record.settlement, "recoverable");
			assert.equal(domains[0].child.signalCode, "SIGTERM");
			assert.equal(events().filter((entry) => entry.event === "session/cancel").length, 1);
			assert.equal(events().filter((entry) => entry.event === "prompt/start").length, 1);
			assert.ok(!transitions.includes("idle"), "held claim cannot publish idle");
			if (mode === "ignore") assert.match(control.record.error, /timed out/);
			else assert.equal(control.record.stopReason, "cancelled");
			const count = polls;
			await until(() => polls >= count + 3);
			assert.equal(domains.length, 1, "no automatic redispatch of old instructions");
			await requestControl(config, request("continue", active, revised));
			await until(() => domains.length === 2 && control.record.status !== "continuation-queued" && control.record.domainExited && !control.active);
			assert.equal(control.record.acknowledged, mode !== "no-ack");
			assert.equal(control.record.hold, mode === "no-ack");
			const prompts = events().filter((entry) => entry.event === "prompt/start");
			assert.equal(prompts.length, 2);
			assert.equal(prompts[0].sessionId, prompts[1].sessionId);
			assert.ok(prompts[1].text.includes(revised.spec));
			assert.ok(prompts[1].text.includes(revised.changes));
			assert.match(prompts[1].text, /succeed at the standalone claim/);
			assert.ok(events().some((entry) => entry.event === "session/load"));
		} finally {
			controller.abort();
			await running;
			for (const session of domains) assert.ok(session.child.exitCode !== null || session.child.signalCode !== null);
		}
	});
}

test("operator unproved teardown retains an actionable durable fence", async () => {
	const { config } = rig();
	const control = new OperatorControl(config);
	let done;
	const running = runBridge(config, { operator: control, logger: quiet,
		loadInstructions: async () => ({ instructions: "role" }), runWait: async () => envelope(),
		runtime: { start: async () => {}, facts: async () => {}, state: async () => {}, end: async () => {}, incident: async () => true },
		sessionFactory: () => ({ sessionId: "s", alive: () => true, start: async () => "s",
			promptText: () => new Promise((resolve) => { done = resolve; }),
			cancel: () => done({ stopReason: "cancelled" }),
			stop: async () => { throw new DomainTeardownError("fixture domain still running"); } }) });
	const failed = assert.rejects(running, /fixture domain still running/);
	await until(() => control.active);
	control.handle(request("cancel", control.status().active));
	await failed;
	assert.equal(control.record.status, "domain-unsettled");
	assert.equal(control.record.domainExited, false);
	assert.equal(control.record.hold, true);
});

test("continuation refuses a replaced ACP session without sending a prompt", async () => {
	const { config } = rig();
	const control = new OperatorControl(config);
	await control.start();
	try {
		const active = await held(control);
		control.handle(request("continue", active, revised));
		let sent = false;
		await assert.rejects(control.prompt({ sessionId: "replacement", promptText: async () => { sent = true; } }, "old", envelope(), action), /session mismatch/);
		assert.equal(sent, false);
		assert.equal(control.record.hold, true);
		assert.equal(control.pending, null);
	} finally { await control.close(); }
});
