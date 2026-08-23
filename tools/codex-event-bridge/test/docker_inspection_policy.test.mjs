// W2845: the bounded read-only Docker inspection profile.
//
// `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
// finding-v12-local-isolated-execution/findings/
// finding-managed-docker-inspection-policy/`.
//
// Two managed `baton.codex` review turns were quarantined after asking
// for interactive approval to run `docker version --format '{{json .}}'`.
// The dispatcher denied correctly and a restart minted a fresh context,
// but neither changed the execution policy, so the same research step
// failed again. The operator then hand-added four rules to the live
// policy file — which is the hand editing the generator exists to
// replace.
//
// The confirmed boundary is FOUR read-only prefixes. Unrestricted
// `docker` is not authorized: it can mount host paths or the runtime
// socket, run privileged containers, and destroy containers, images,
// networks and volumes outside the filesystem sandbox. Mutable OCI
// lifecycle operations belong behind the trusted Worker Manager's
// validated runtime adapter.
//
// Every case below writes the expected rules out LITERALLY rather than
// reading them from the module under test, because a module compared
// with itself can authorize anything and still pass.

import test from "node:test";
import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { mkdtempSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { validateConfig } from "../src/config.mjs";
import { EventBridge } from "../src/event_bridge.mjs";
import {
	assertInspectionProvisioned,
	assertPolicyProvisioned,
	auditInspectionRules,
	auditRules,
	inspectionRules,
	rulesFor,
	DOCKER_INSPECTIONS,
	INSPECTION_PROFILE,
} from "../src/exec_policy.mjs";
import { freshQuarantineDir } from "./quarantine_fixture.mjs";

// The approved set, in the ruled order.
const INSPECTIONS = [
	'prefix_rule(pattern=["docker", "version"], decision="allow")',
	'prefix_rule(pattern=["docker", "info"], decision="allow")',
	'prefix_rule(pattern=["docker", "inspect"], decision="allow")',
	'prefix_rule(pattern=["docker", "image", "inspect"], decision="allow")',
];

// Representative MUTABLE and otherwise-unruled Docker commands. This is
// a sample for the regressions, never the implementation's test: the
// module recognises the four ruled prefixes and treats everything else
// as outside the profile, so it needs no list of forbidden subcommands
// to keep in step with Docker's grammar.
const MUTABLE = [
	["docker", "run", "--privileged", "-v", "/:/host", "alpine"],
	["docker", "exec", "-it", "worker", "sh"],
	["docker", "rm", "-f", "worker"],
	["docker", "rmi", "worker:latest"],
	["docker", "image", "rm", "worker:latest"],
	["docker", "build", "-t", "worker", "."],
	["docker", "pull", "alpine"],
	["docker", "push", "worker:latest"],
	["docker", "stop", "worker"],
	["docker", "kill", "worker"],
	["docker", "volume", "prune", "-f"],
	["docker", "network", "create", "escape"],
	["docker", "system", "prune", "-af"],
	["docker", "cp", "worker:/etc/shadow", "."],
	["docker", "login", "-u", "ops"],
	// Read-only but UNRULED. The ruling named four prefixes; a fifth is
	// a decision to obtain, not one to make while implementing.
	["docker", "ps", "-a"],
	["docker", "logs", "worker"],
	["docker", "stats", "--no-stream"],
];

const IDENTITY = { binary: "/opt/baton/bin/baton",
	config: "/srv/baton/baton.json", participant: "baton.codex" };
const EXACT_BATON = rulesFor(IDENTITY).join("\n");
const EXACT_INSPECTION = INSPECTIONS.join("\n");
const dir = mkdtempSync("/tmp/w2845-inspection-policy-");
let serial = 0;

function write(text) {
	const file = join(dir, `policy-${serial++}.rules`);
	writeFileSync(file, `${text}\n`);
	return file;
}

function allow(argv) {
	return `prefix_rule(pattern=[${argv.map((entry) => JSON.stringify(entry))
		.join(", ")}], decision="allow")`;
}

test("W2845: the module publishes exactly the confirmed inspection profile",
	() => {
		assert.equal(INSPECTION_PROFILE, "managed-docker-inspection");
		assert.deepEqual(DOCKER_INSPECTIONS, [
			["docker", "version"],
			["docker", "info"],
			["docker", "inspect"],
			["docker", "image", "inspect"],
		], "the ruled inspection set drifted from the confirmed boundary; "
			+ "widening it is a ruling to obtain, not an implementation decision");
		// Order is part of the ruling: an operator diffing a regenerated
		// file against the record should see no reordering noise.
		assert.deepEqual(inspectionRules(), INSPECTIONS);
	});

test("W2845: the exact four rules satisfy the inspection preflight", () => {
	const audit = auditInspectionRules(EXACT_INSPECTION);
	assert.deepEqual(audit.missing, []);
	assert.deepEqual(audit.broad, []);
	assert.deepEqual(audit.extra, []);
	assert.equal(audit.satisfied, true);
	assert.equal(assertInspectionProvisioned(write(EXACT_INSPECTION)).satisfied,
		true);
	// And they satisfy it beside a complete Baton policy, which is the
	// state the deployment is actually in.
	assert.equal(assertInspectionProvisioned(
		write(`${EXACT_BATON}\n${EXACT_INSPECTION}`)).satisfied, true);
});

test("W2845: an absent inspection rule fails the preflight", () => {
	// The defect itself: the policy authorized every Baton verb and no
	// Docker command at all, so the research step escalated for
	// interactive approval and the context was quarantined.
	const audit = auditInspectionRules(EXACT_BATON);
	assert.deepEqual(audit.missing,
		["docker version", "docker info", "docker inspect", "docker image inspect"]);
	assert.equal(audit.satisfied, false);
	assert.throws(() => assertInspectionProvisioned(write(EXACT_BATON)),
		/does not authorize \[docker version, docker info, docker inspect, docker image inspect\]/);
	// A partial file names only what is actually absent, and the
	// refusal carries the exact rules to install.
	const partial = INSPECTIONS.slice(0, 2).join("\n");
	assert.deepEqual(auditInspectionRules(partial).missing,
		["docker inspect", "docker image inspect"]);
	try {
		assertInspectionProvisioned(write(partial));
		assert.fail("should have refused");
	} catch (error) {
		for (const rule of INSPECTIONS) assert.ok(error.message.includes(rule));
		assert.match(error.message, /would be quarantined unclaimed/);
	}
});

test("W2845: an UNRESTRICTED docker rule is refused, not counted as coverage",
	() => {
		// The whole point of the ruling. `docker` alone covers all four
		// inspections AND every destructive command beside them.
		const broad = auditInspectionRules(allow(["docker"]));
		assert.deepEqual(broad.missing, [], "it does technically cover them");
		assert.equal(broad.broad.length, 4);
		assert.equal(broad.satisfied, false,
			"broad coverage is not satisfaction");
		assert.throws(() => assertInspectionProvisioned(write(allow(["docker"]))),
			/contains a BROADER Docker rule/);

		// The half-finished upgrade an operator most likely has: the
		// exact rules added and the broad one left behind. A narrow rule
		// does not cancel a broad one; both are simply there.
		const mixed = `${EXACT_INSPECTION}\n${allow(["docker"])}`;
		assert.deepEqual(auditInspectionRules(mixed).missing, []);
		assert.equal(auditInspectionRules(mixed).broad.length, 4);
		assert.equal(auditInspectionRules(mixed).satisfied, false);
		assert.throws(() => assertInspectionProvisioned(write(mixed)),
			/A narrow rule does not cancel a broad one/);

		// `docker image` is the other broad shape, and the one an
		// operator might reach for while reading the fourth prefix. It
		// authorizes `docker image rm`.
		const group = `${EXACT_INSPECTION}\n${allow(["docker", "image"])}`;
		const audit = auditInspectionRules(group);
		assert.deepEqual(audit.broad,
			[{ command: "docker image inspect", by: ["docker image"] }]);
		assert.equal(audit.satisfied, false);
		assert.throws(() => assertInspectionProvisioned(write(group)),
			/BROADER Docker rule \[docker image\]/);
	});

test("W2845: every mutable or unruled Docker command is extra capability",
	() => {
		for (const argv of MUTABLE) {
			const policy = `${EXACT_INSPECTION}\n${allow(argv)}`;
			const audit = auditInspectionRules(policy);
			assert.deepEqual(audit.missing, [], argv.join(" "));
			assert.deepEqual(audit.broad, [], argv.join(" "));
			assert.deepEqual(audit.extra, [argv.join(" ")],
				`${argv.join(" ")} was not seen as extra capability`);
			assert.equal(audit.satisfied, false, argv.join(" "));
			assert.throws(() => assertInspectionProvisioned(write(policy)),
				/dedicated to the approved 'managed-docker-inspection' set/,
				argv.join(" "));
		}
		// The refusal names the approved set and where mutation belongs,
		// so the operator does not have to go looking for either.
		try {
			assertInspectionProvisioned(write(
				`${EXACT_INSPECTION}\n${allow(["docker", "run", "alpine"])}`));
			assert.fail("should have refused");
		} catch (error) {
			for (const command of DOCKER_INSPECTIONS) {
				assert.ok(error.message.includes(command.join(" ")));
			}
			assert.match(error.message, /trusted Worker Manager/);
		}
	});

test("W2845: a ruled inspection carrying operands is a subset, not extra",
	() => {
		// The command the quarantined turns actually ran. A rule for it
		// authorizes less than `docker version` already does, so it is
		// not extra capability — the same reasoning the Baton audit
		// applies to a ruled verb carrying operands.
		const qualified = [
			["docker", "version", "--format", "{{json .}}"],
			["docker", "inspect", "--format", "{{json .}}", "worker"],
			["docker", "image", "inspect", "worker:latest"],
			["docker", "info", "--format", "{{json .}}"],
		];
		for (const argv of qualified) {
			const audit = auditInspectionRules(
				`${EXACT_INSPECTION}\n${allow(argv)}`);
			assert.deepEqual(audit.extra, [], argv.join(" "));
			assert.equal(audit.satisfied, true, argv.join(" "));
		}
		// But it does not COVER the ruled prefix on its own: a policy
		// holding only the qualified form leaves the general inspection
		// unauthorized, and the turn still escalates.
		const only = allow(["docker", "version", "--format", "{{json .}}"]);
		assert.ok(auditInspectionRules(only).missing.includes("docker version"));
	});

test("W2845: a docker rule this generator did not spell is still seen", () => {
	// The auditor recognises any executable slot naming docker, not
	// just the bare spelling it emits. An absolute-path mutable rule is
	// exactly the capability the ruling withholds, and an auditor blind
	// to it would call the file clean.
	for (const argv of [["/usr/bin/docker", "run", "alpine"],
	                    ["/usr/local/bin/docker", "rm", "-f", "worker"]]) {
		const audit = auditInspectionRules(`${EXACT_INSPECTION}\n${allow(argv)}`);
		assert.deepEqual(audit.extra, [argv.join(" ")]);
		assert.equal(audit.satisfied, false);
	}
	// An absolute-path INSPECTION rule is reported too. It is a
	// different command string from the ruled prefix, and the auditor
	// cannot know that path resolves to the same binary — so it is
	// reported rather than assumed equivalent.
	const absolute = allow(["/usr/bin/docker", "version"]);
	assert.deepEqual(auditInspectionRules(`${EXACT_INSPECTION}\n${absolute}`).extra,
		["/usr/bin/docker version"]);
	// A rule whose executable merely CONTAINS docker is not a docker
	// rule; `docker-compose` is outside this ruling either way.
	assert.deepEqual(
		auditInspectionRules(`${EXACT_INSPECTION}\n${allow(["docker-compose", "up"])}`)
			.extra, []);
});

test("W2845: a restricting rule is never inspection coverage", () => {
	// Round 4 of the review: this case used to spell the restriction
	// `decision="deny"`, which the installed evaluator REFUSES — so it
	// asserted the audit's answer about a file Codex will not load, and
	// stood as a semantic oracle it was never entitled to be. The
	// evaluator's decision domain is `allow`, `prompt` and `forbidden`
	// (measured; see `EVALUATOR_DECISIONS`), so the restriction this case
	// needs is `forbidden`. `deny` now has its own unaccounted case below.
	const restricted = EXACT_INSPECTION.replaceAll('"allow"', '"forbidden"');
	const audit = auditInspectionRules(restricted);
	assert.deepEqual(audit.unaccounted, [],
		"a valid restriction must still be READ, or the refusal is fail-blind");
	assert.equal(audit.missing.length, 4);
	assert.deepEqual(audit.extra, [],
		"a forbidden rule is a restriction, not capability");
	assert.throws(() => assertInspectionProvisioned(write(restricted)),
		/does not authorize/);
});

test("W2845: an unreadable policy is a refusal, not an assumption", () => {
	assert.throws(() => assertInspectionProvisioned(join(dir, "absent.rules")),
		/is unreadable/);
});

test("W2845: the two profiles audit independently on the one file", () => {
	// The dispatcher preflights ONE nominated file for both. Neither
	// audit may see the other's rules as a defect, or provisioning both
	// would be impossible.
	const both = `${EXACT_BATON}\n${EXACT_INSPECTION}`;
	assert.equal(auditRules(both, IDENTITY).satisfied, true,
		"the inspection rules were counted against the Baton profile");
	assert.deepEqual(auditRules(both, IDENTITY).extra, []);
	assert.equal(auditInspectionRules(both).satisfied, true,
		"the Baton rules were counted against the inspection profile");
	assert.equal(assertPolicyProvisioned(write(both), IDENTITY).satisfied, true);
	assert.equal(assertInspectionProvisioned(write(both)).satisfied, true);
	// And a Docker defect does not become a Baton defect: an
	// unrestricted docker rule leaves the Baton audit clean, so the two
	// refusals stay separately actionable.
	const loose = `${both}\n${allow(["docker"])}`;
	assert.equal(auditRules(loose, IDENTITY).satisfied, true);
	assert.equal(auditInspectionRules(loose).satisfied, false);
});

test("W2845: the dispatcher refuses to start on an unprovisioned inspection",
	() => {
		// A dispatcher whose managed research turns escalate on
		// `docker version` is the defect this Work records; it must not
		// open leases and report itself healthy in that state.
		const start = (policy) => {
			const config = validateConfig({
				roleInstructions: { binary: IDENTITY.binary,
					config: IDENTITY.config, execPolicyFile: policy },
				servers: { local: { endpoint: "ws://127.0.0.1:4500" } },
				targets: { reviewer: { server: "local", threadId: "thread-a",
					identity: { participant: IDENTITY.participant, role: "rview",
						actionOwner: "baton.slaw" } } },
				eventSocket: "/tmp/codex-event-bridge-w2845-unused.sock",
				quarantineDir: freshQuarantineDir(),
			});
			// The client is constructed with the bridge but must never
			// CONNECT: the preflight runs before anything opens.
			const client = Object.assign(new EventEmitter(), {
				connectAndInitialize() {
					throw new Error("the preflight let a connection open");
				},
			});
			const bridge = new EventBridge({
				config,
				logger: { info() {}, warn() {}, error() {}, debug() {} },
				clientFactory: () => client,
			});
			return bridge.start({ listen: false });
		};
		// Baton-complete but with no inspection at all.
		return Promise.all([
			assert.rejects(() => start(write(EXACT_BATON)),
				/does not authorize \[docker version/),
			assert.rejects(
				() => start(write(`${EXACT_BATON}\n${allow(["docker"])}`)),
				/contains a BROADER Docker rule/),
			assert.rejects(
				() => start(write(`${EXACT_BATON}\n${EXACT_INSPECTION}\n`
					+ allow(["docker", "run", "--privileged", "alpine"]))),
				/dedicated to the approved 'managed-docker-inspection' set/),
		]);
	});
