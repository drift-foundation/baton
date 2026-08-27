// W424: a bootstrapped Codex thread must outlive its bootstrap client.
//
// `work/records/2026/08/finding-codex-bootstrap-thread-durability/`.
// During the 975af64 cutover `--start-thread` printed a new tuner
// thread id and exited 0. The dispatcher could not resume it:
//
//     thread/resume failed (-32600): no rollout found for thread id ...
//
// and neither could a second client one second later, with no restart
// in between. `thread/start` alone creates no rollout, so the command
// was reporting success for a locator that did not exist yet — and the
// deployment recorded it, restarted the dispatcher, and left W321
// queued and overdue behind a target that could never load.
//
// What these tests hold: the supported path records a first turn and
// then PROVES the thread resumes on a second connection before any
// locator reaches stdout, and every way that can fail fails the
// command instead of printing something usable-looking.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { BOOTSTRAP_PROMPT, bootstrapThread } from "../src/main.mjs";
import { launcherContract } from "../src/role_instructions.mjs";

const OPTIONS = {
	endpoint: "ws://127.0.0.1:4500",
	cwd: "/home/op/src/baton",
	baton: "/opt/baton/bin/baton",
	"baton-config": "/home/op/baton.json",
	participant: "baton.tuner",
	role: "tuner",
};

const ROLE = {
	instructions: "You are the tuner for baton.",
	participant: "baton.tuner",
	role: "tuner",
	configurationGeneration: 4,
};

const quiet = { info() {}, warn() {}, error() {}, debug() {} };

/** An app-server that models the ONE property this Work is about:
 *  a thread is resumable only once it holds a completed turn. */
class FakeServer {
	constructor({ persistOnTurn = true } = {}) {
		this.threads = new Map();
		this.persistOnTurn = persistOnTurn;
		this.clients = [];
		this.next = 1;
	}

	client(name) {
		const client = new FakeClient(this, name);
		this.clients.push(client);
		return client;
	}

	start() {
		const id = `thread-${this.next++}`;
		// exactly the observed shape: an id exists, a rollout does not
		this.threads.set(id, { durable: false, turns: [] });
		return id;
	}

	turn(id, text) {
		const thread = this.threads.get(id);
		if (!thread) throw new Error(`no such thread ${id}`);
		thread.turns.push(text);
		if (this.persistOnTurn) thread.durable = true;
		return `turn-${thread.turns.length}`;
	}

	resume(id) {
		const thread = this.threads.get(id);
		if (!thread || !thread.durable) {
			throw new Error(
				`thread/resume failed (-32600): no rollout found for thread id ${id}`);
		}
		return thread;
	}
}

class FakeClient extends EventEmitter {
	constructor(server, name) {
		super();
		this.server = server;
		this.name = name;
		this.connected = false;
		this.disconnected = false;
		this.turnStatus = "completed";
		this.failTurnStart = null;
	}

	async connectAndInitialize() {
		this.connected = true;
	}

	async startThread({ cwd, developerInstructions }) {
		this.startedWith = { cwd, developerInstructions };
		const id = this.server.start();
		return { thread: { id, status: { type: "idle" }, turns: [] } };
	}

	async startTurn(threadId, text, clientId) {
		if (this.failTurnStart) throw new Error(this.failTurnStart);
		this.turnText = text;
		this.clientId = clientId;
		const id = this.server.turn(threadId, text);
		// Recorded rather than emitted: a completion that fires before
		// the caller has registered its wait is a property of the real
		// client's event ordering, not something this fake should be
		// able to lose.
		this.completion = { threadId, turn: { id, status: this.turnStatus } };
		return { id, status: "inProgress" };
	}

	async waitForTurnCompletion(threadId, turnId) {
		const done = this.completion;
		if (!done || done.threadId !== threadId || done.turn.id !== turnId) {
			throw new Error(`no completion recorded for ${turnId}`);
		}
		return done.turn;
	}

	async resume(threadId) {
		if (!this.connected) throw new Error("not connected");
		this.server.resume(threadId);
		return { thread: { id: threadId, status: { type: "idle" } } };
	}

	disconnect() {
		this.connected = false;
		this.disconnected = true;
	}
}

function capture() {
	const written = [];
	return {
		written,
		out: { write: (chunk) => { written.push(String(chunk)); return true; } },
		text: () => written.join(""),
	};
}

async function run(server, { options = OPTIONS, read, prepare } = {}) {
	const made = [];
	const sink = capture();
	const code = await bootstrapThread(options, quiet, {
		out: sink.out,
		read: read ?? (async () => ROLE),
		clientFactory: (name) => {
			const client = server.client(name);
			made.push(client);
			prepare?.(client, made.length);
			return client;
		},
	});
	return { code, written: sink.text(), made };
}

// -- the supported path ------------------------------------------------------

test("the bootstrap records a first turn before it reports anything",
	async () => {
		const server = new FakeServer();
		const { code, written, made } = await run(server);
		assert.equal(code, 0);
		const [creator] = made;
		assert.equal(creator.turnText, BOOTSTRAP_PROMPT);
		assert.ok(creator.clientId, "the turn carried no client message id");
		const [id] = [...server.threads.keys()];
		assert.deepEqual(server.threads.get(id).turns, [BOOTSTRAP_PROMPT]);
		assert.equal(JSON.parse(written).threadId, id);
	});

test("the turn is a no-tool instruction, not work", () => {
	assert.match(BOOTSTRAP_PROMPT, /Do not run any command/);
	assert.match(BOOTSTRAP_PROMPT, /use any tool/);
});

test("the thread is proved resumable on a SECOND connection", async () => {
	// The observed failure was not "the creator cannot read it" — the
	// creator could. It was that nobody else could.
	const server = new FakeServer();
	const { made } = await run(server);
	assert.equal(made.length, 2, "only one connection was used");
	assert.equal(made[0].disconnected, true,
		"the creating connection was still open when resume was proved");
	assert.equal(made[1].disconnected, true,
		"the verifying connection was left open");
});

test("the locator carries the resolved identity and generation",
	async () => {
		const { written } = await run(new FakeServer());
		assert.deepEqual(JSON.parse(written), {
			threadId: "thread-1",
			participant: "baton.tuner",
			role: "tuner",
			configurationGeneration: 4,
		});
	});

test("the accepted role instructions AND the launcher contract reach "
	+ "thread/start", async () => {
	// W12229 replaced this assertion, and the old one is the defect: it
	// required `developerInstructions` to be the role prose and NOTHING
	// else, which is exactly the fresh `pc.plan` context that reached
	// W12181 over and over and could not claim it because it had never
	// been told which executable, config, participant or role to use.
	const server = new FakeServer();
	const { made } = await run(server);
	assert.deepEqual(made[0].startedWith, {
		cwd: OPTIONS.cwd,
		developerInstructions: `${ROLE.instructions}\n\n`
			+ launcherContract({
				binary: OPTIONS.baton, config: OPTIONS["baton-config"],
				participant: ROLE.participant, role: ROLE.role }),
	});
});

test("the launcher contract carries exactly the ruled four values", async () => {
	const server = new FakeServer();
	const { made } = await run(server);
	const text = made[0].startedWith.developerInstructions;
	assert.match(text, /BATON_BIN="\/opt\/baton\/bin\/baton"/);
	assert.match(text, /BATON_CONFIG="\/home\/op\/baton.json"/);
	assert.match(text, /BATON_PARTICIPANT="baton.tuner"/);
	assert.match(text, /BATON_ROLE="tuner"/);
	// And nothing beside them. An action owner, an exec-policy path or a
	// scrap of configuration would each be a value nobody ruled into a
	// durable persona.
	assert.equal(text.includes("actionOwner"), false);
	assert.equal(text.includes("execPolicy"), false);
	assert.equal((text.match(/^BATON_/gm) ?? []).length, 4,
		"the block carries something other than the four ruled fields");
});

test("the role prose comes first and the contract is appended once",
	async () => {
	const server = new FakeServer();
	const { made } = await run(server);
	const text = made[0].startedWith.developerInstructions;
	assert.ok(text.startsWith(ROLE.instructions),
		"the accepted role prose was altered rather than composed with");
	assert.equal(
		(text.match(/Baton launcher contract \(authoritative/g) ?? []).length,
		1, "the contract was rendered more than once");
});

test("--start-thread refuses before any read when a contract field is absent",
	async () => {
	// All four fail in the same place now. `--role` used to be refused
	// indirectly by the instruction reader, so one field of one contract
	// failed later and in somebody else's error.
	for (const missing of ["endpoint", "cwd", "baton", "baton-config",
	                       "participant", "role"]) {
		const options = { ...OPTIONS };
		delete options[missing];
		let read = 0;
		let connected = 0;
		await assert.rejects(
			bootstrapThread(options, quiet, {
				out: capture().out,
				read: async () => { read += 1; return ROLE; },
				clientFactory: () => { connected += 1; return null; },
			}),
			new RegExp(`--start-thread requires --${missing}`),
			`a missing --${missing} did not refuse`);
		assert.equal(read, 0, `--${missing} was read past`);
		assert.equal(connected, 0, `--${missing} reached a Codex connection`);
	}
});

test("--start-thread refuses a relative Baton source before reading it",
	async () => {
	// Resolving either path through PATH or the bridge's working directory
	// is inference. The configured dispatcher already refuses this shape;
	// fresh bootstrap must enforce the same launcher contract before its
	// instruction read or Codex connection.
	for (const [name, value] of [["baton", "bin/baton"],
	                            ["baton-config", "state/baton.json"]]) {
		const options = { ...OPTIONS, [name]: value };
		let reads = 0;
		let connections = 0;
		await assert.rejects(
			bootstrapThread(options, quiet, {
				out: capture().out,
				read: async () => { reads += 1; return ROLE; },
				clientFactory: () => { connections += 1; return null; },
			}),
			new RegExp(`--${name}.*absolute`),
			`a relative --${name} was accepted as canonical`);
		assert.equal(reads, 0, `--${name} reached the instruction read`);
		assert.equal(connections, 0, `--${name} reached a Codex connection`);
	}
});

test("the two entry points refuse the same relative shape", async () => {
	// The defect was that they did not. `validateConfig` has always
	// required both `roleInstructions` paths to be absolute, and
	// standalone bootstrap never passes through it — so one contract had
	// two different admission rules depending on which door it came in.
	const { validateConfig } = await import("../src/config.mjs");
	for (const [field, value] of [["binary", "bin/baton"],
	                              ["config", "state/baton.json"]]) {
		const source = { binary: "/opt/baton/bin/baton",
			config: "/home/op/baton.json",
			execPolicyFile: "/opt/baton/policy.json", [field]: value };
		assert.throws(() => validateConfig({
			roleInstructions: source,
			servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
			targets: { one: { server: "local", threadId: "t",
				identity: { participant: "baton.tuner", role: "tuner",
					actionOwner: "ops.slaw" } } },
			eventSocket: "/tmp/codex-w12229.sock",
			quarantineDir: "/tmp/codex-w12229-quarantine",
		}), /must be an absolute path/,
			`the dispatcher accepted a relative ${field}`);
	}
	// And the same two shapes at the bootstrap door.
	for (const [name, value] of [["baton", "bin/baton"],
	                             ["baton-config", "state/baton.json"]]) {
		await assert.rejects(
			bootstrapThread({ ...OPTIONS, [name]: value }, quiet, {
				out: capture().out,
				read: async () => ROLE,
				clientFactory: () => null,
			}),
			new RegExp(`--${name}.*absolute`));
	}
});

test("a path that merely LOOKS rooted is not absolute", async () => {
	// The kind of value a launcher template produces when a variable did
	// not expand: it has the shape of a path and none of the meaning.
	for (const value of ["./bin/baton", "../baton/bin/baton", "bin/baton",
	                     "~/baton/bin/baton", "$BATON_HOME/bin/baton"]) {
		await assert.rejects(
			bootstrapThread({ ...OPTIONS, baton: value }, quiet, {
				out: capture().out,
				read: async () => ROLE,
				clientFactory: () => null,
			}),
			/--baton.*absolute/,
			`${value} was accepted as an absolute executable`);
	}
});

test("an absolute pair still reaches the read and the contract", async () => {
	// The other half: the guard refuses a shape, not the ordinary case.
	const server = new FakeServer();
	const { made } = await run(server);
	assert.match(made[0].startedWith.developerInstructions,
		/BATON_BIN="\/opt\/baton\/bin\/baton"/);
});

test("a launcher contract field that is blank refuses rather than rendering "
	+ "a hole", async () => {
	for (const spoiled of [{ binary: "" }, { config: "   " },
	                       { participant: undefined }, { role: null }]) {
		assert.throws(() => launcherContract({
			binary: "/opt/baton/bin/baton", config: "/home/op/baton.json",
			participant: "baton.tuner", role: "tuner", ...spoiled }),
			/needs an explicit/,
			`${JSON.stringify(spoiled)} rendered a partial contract`);
	}
});

test("the contract quotes its values so a path is data, not syntax",
	async () => {
	const text = launcherContract({
		binary: "/opt/baton bin/ba\"ton", config: "/home/op/b c.json",
		participant: "pc.plan", role: "rview" });
	assert.match(text, /BATON_BIN="\/opt\/baton bin\/ba\\"ton"/);
	assert.match(text, /BATON_CONFIG="\/home\/op\/b c.json"/);
});

test("the renderer reads nothing and infers nothing", async () => {
	// Conflicting ambient values and a plausible repository path must not
	// reach the block: a context that could be told the wrong executable
	// by an environment variable is a context that infers.
	const before = { ...process.env };
	process.env.BATON_BIN = "/wrong/baton";
	process.env.BATON_CONFIG = "/wrong/baton.json";
	process.env.BATON_PARTICIPANT = "somebody.else";
	process.env.BATON_ROLE = "approv";
	try {
		const text = launcherContract({
			binary: "/opt/baton/bin/baton", config: "/home/op/baton.json",
			participant: "baton.tuner", role: "tuner" });
		assert.equal(text.includes("/wrong/"), false);
		assert.equal(text.includes("somebody.else"), false);
		assert.equal(text.includes("approv"), false);
	} finally {
		for (const name of ["BATON_BIN", "BATON_CONFIG", "BATON_PARTICIPANT",
		                    "BATON_ROLE"]) {
			if (before[name] === undefined) delete process.env[name];
			else process.env[name] = before[name];
		}
	}
});

// -- every way it can fail, fails the command --------------------------------

test("a thread that cannot be resumed fails instead of printing an id",
	async () => {
		// The exact production defect: `thread/start` returns an id and
		// no rollout follows it.
		const server = new FakeServer({ persistOnTurn: false });
		const sink = capture();
		await assert.rejects(
			bootstrapThread(OPTIONS, quiet, {
				out: sink.out,
				read: async () => ROLE,
				clientFactory: (name) => server.client(name),
			}),
			/could not resume it/);
		assert.equal(sink.text(), "",
			"an unusable locator was printed anyway");
	});

test("the refusal names the thread so an operator can clean it up",
	async () => {
		const server = new FakeServer({ persistOnTurn: false });
		await assert.rejects(
			bootstrapThread(OPTIONS, quiet, {
				read: async () => ROLE,
				clientFactory: (name) => server.client(name),
			}),
			/thread-1/);
	});

test("a turn that does not complete fails the bootstrap", async () => {
	const server = new FakeServer();
	const sink = capture();
	await assert.rejects(
		bootstrapThread(OPTIONS, quiet, {
			out: sink.out,
			read: async () => ROLE,
			clientFactory: (name) => {
				const client = server.client(name);
				client.turnStatus = "failed";
				return client;
			},
		}),
		/NOT reported as usable/);
	assert.equal(sink.text(), "");
});

test("a turn that cannot be started fails the bootstrap", async () => {
	const server = new FakeServer();
	const sink = capture();
	await assert.rejects(
		bootstrapThread(OPTIONS, quiet, {
			out: sink.out,
			read: async () => ROLE,
			clientFactory: (name) => {
				const client = server.client(name);
				client.failTurnStart = "turn/start refused";
				return client;
			},
		}),
		/could not record a first turn for thread-1/);
	assert.equal(sink.text(), "");
});

test("the creating connection is closed even when the turn fails",
	async () => {
		const server = new FakeServer();
		const made = [];
		await assert.rejects(bootstrapThread(OPTIONS, quiet, {
			read: async () => ROLE,
			clientFactory: (name) => {
				const client = server.client(name);
				client.failTurnStart = "turn/start refused";
				made.push(client);
				return client;
			},
		}));
		assert.equal(made[0].disconnected, true,
			"a failed bootstrap left its connection open");
	});

test("a missing operand still refuses before any connection", async () => {
	const server = new FakeServer();
	for (const name of ["endpoint", "cwd", "baton", "baton-config",
	                    "participant"]) {
		const options = { ...OPTIONS };
		delete options[name];
		await assert.rejects(
			bootstrapThread(options, quiet, {
				read: async () => ROLE,
				clientFactory: () => server.client("unused"),
			}),
			new RegExp(`requires --${name}`));
	}
	assert.equal(server.clients.length, 0,
		"a refused bootstrap opened a connection anyway");
});

test("an unresolvable role fails before a thread is created", async () => {
	const server = new FakeServer();
	await assert.rejects(
		bootstrapThread(OPTIONS, quiet, {
			read: async () => { throw new Error("no such role"); },
			clientFactory: (name) => server.client(name),
		}),
		/no such role/);
	assert.equal(server.threads.size, 0);
});
