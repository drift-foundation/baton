// Unit tests for the prototype's fail-closed boundaries. These cover
// the parts the end-to-end proof cannot demonstrate cheaply: every way
// a claim token is supposed to be refused, the mount assertions, the
// manifest rules, and the two evidence bugs found while building this
// (a trace payload overwriting the trace's own ordering field, and an
// over-eager redaction hiding the negative proof's own subject).

import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, mkdirSync, readFileSync, symlinkSync,
         writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { ClaimTokenIssuer, TokenError } from "../src/claim_token.mjs";
import { envelope, validate, EnvelopeError } from "../src/envelopes.mjs";
import { assertContained, manifestOf, ManifestError } from "../src/manifest.mjs";
import { diffIndex, expectedIndex, headingOf } from "../src/fixture_check.mjs";
import { runArgv, ContainerError } from "../src/container.mjs";
import { parseFencedJson, ReplyError } from "../src/prompts.mjs";
import { Trace, redact } from "../src/trace.mjs";
import { assertNoBatonCapability, assertPreClaimPosture, attemptPaths as attemptPathsFor,
         preClaimSpec,
         stageCredentials, RuntimeError } from "../src/runtime.mjs";
import { BatonClient, validateReadiness, BatonError } from "../src/baton_cli.mjs";

const scratch = () => mkdtempSync(join(tmpdir(), "v12poc-test-"));

const BINDING = { work: "W2", participant: "poc.claude", runtime_attempt: "a1" };
const mintArgs = { work: "W2", participant: "poc.claude", runtimeAttempt: "a1",
                   offerDigest: "d0" };

test("a freshly minted token validates against its exact binding", () => {
	const issuer = new ClaimTokenIssuer();
	const { token, payload } = issuer.mint(mintArgs);
	assert.equal(issuer.validate(token, BINDING).jti, payload.jti);
});

test("an expired token is refused, and expiry is judged by the manager's clock", () => {
	let now = 1000;
	const issuer = new ClaimTokenIssuer({ ttlMs: 50, now: () => now });
	const { token } = issuer.mint(mintArgs);
	now = 1051;
	assert.throws(() => issuer.validate(token, BINDING),
		(error) => error instanceof TokenError && error.reason === "expired");
});

test("a spent token is refused on replay", () => {
	const issuer = new ClaimTokenIssuer();
	const { token, payload } = issuer.mint(mintArgs);
	issuer.spend(payload.jti);
	assert.throws(() => issuer.validate(token, BINDING),
		(error) => error.reason === "replayed");
	// And spending twice is refused too: the fence does not depend on
	// the caller remembering not to try.
	assert.throws(() => issuer.spend(payload.jti), (error) => error.reason === "replayed");
});

test("a token minted for another Work, participant or attempt is refused", () => {
	const issuer = new ClaimTokenIssuer();
	const { token } = issuer.mint(mintArgs);
	for (const [field, value] of [["work", "W9"], ["participant", "poc.rev"],
	                              ["runtime_attempt", "a2"]]) {
		assert.throws(() => issuer.validate(token, { ...BINDING, [field]: value }),
			(error) => error.reason === "misbound", `${field} must be checked`);
	}
});

test("a token this manager run did not mint is refused even when well formed", () => {
	const other = new ClaimTokenIssuer();
	const { token } = other.mint(mintArgs);
	const mine = new ClaimTokenIssuer({ secret: other.secret });
	// Same secret, so the signature verifies — and it is STILL refused,
	// because single-use is tracked by the issuer that minted it.
	assert.throws(() => mine.validate(token, BINDING), (error) => error.reason === "unknown");
});

test("a tampered signature is refused", () => {
	const issuer = new ClaimTokenIssuer();
	const { token } = issuer.mint(mintArgs);
	const [body] = token.split(".");
	assert.throws(() => issuer.validate(`${body}.AAAA`, BINDING),
		(error) => error.reason === "forged");
});

test("a confident reply with no token at all grants nothing", () => {
	const issuer = new ClaimTokenIssuer();
	issuer.mint(mintArgs);
	for (const reply of [undefined, "", "working", null]) {
		assert.throws(() => issuer.validate(reply, BINDING),
			(error) => error.reason === "absent");
	}
});

test("a refused token is not marked spent", () => {
	let now = 1000;
	const issuer = new ClaimTokenIssuer({ ttlMs: 10000, now: () => now });
	const { token, payload } = issuer.mint(mintArgs);
	assert.throws(() => issuer.validate(token, { ...BINDING, work: "W9" }));
	assert.equal(issuer.issued.get(payload.jti).state, "issued");
	assert.equal(issuer.validate(token, BINDING).jti, payload.jti);
});

test("envelopes refuse an unknown kind, a foreign version and a mistyped field", () => {
	assert.throws(() => validate({ envelope: "nope", version: "0-spike" }), EnvelopeError);
	assert.throws(() => validate({ envelope: "activity", version: "1", ts: "", channel: "", text: "" }),
		/speaks only '0-spike'/);
	assert.throws(() => validate({ envelope: "activity", version: "0-spike", ts: 1, channel: "", text: "" }),
		/activity.ts must be string, got number/);
	assert.throws(() => validate({ envelope: "result", version: "0-spike", work: "W2",
		assignment: {}, outputs: [], status: "accepted" }, "job.out"),
		/expected a 'job.out' envelope, got 'result'/);
	assert.equal(envelope("activity", { ts: "t", channel: "c", text: "x" }).version, "0-spike");
});

test("a manifest is order-independent and refuses symlinks", () => {
	const root = scratch();
	writeFileSync(join(root, "b.txt"), "second");
	writeFileSync(join(root, "a.txt"), "first");
	const first = manifestOf(root);
	assert.deepEqual(first.entries.map((e) => e.path), ["a.txt", "b.txt"]);
	assert.equal(manifestOf(root).digest, first.digest);

	const linked = scratch();
	writeFileSync(join(linked, "real.txt"), "x");
	symlinkSync("/etc/passwd", join(linked, "escape.txt"));
	assert.throws(() => manifestOf(linked), ManifestError);
});

test("containment refuses a result the Job did not declare", () => {
	const root = scratch();
	writeFileSync(join(root, "index.json"), "{}");
	writeFileSync(join(root, "extra.bin"), "x");
	assert.throws(() => assertContained(manifestOf(root), ["index.json"]),
		/contains "extra.bin", which the Job did not declare/);
	assert.doesNotThrow(() => assertContained(manifestOf(root), ["index.json", "extra.bin"]));
});

test("the independent checker reproduces the fixture rule, including its edge cases", () => {
	const root = scratch();
	writeFileSync(join(root, "alpha.md"), "# Alpha\n\nbody\n");
	writeFileSync(join(root, "beta.txt"), "   # Indented\nx\n");
	writeFileSync(join(root, "delta.txt"), "no heading\nsecond\n");
	writeFileSync(join(root, "gamma.md"), "preamble\n\n## Later\n");
	writeFileSync(join(root, "ignored.json"), "{}");
	mkdirSync(join(root, "sub"));
	writeFileSync(join(root, "sub", "deep.md"), "# Deep\n");

	assert.deepEqual(expectedIndex(root), {
		index_version: "0-spike",
		entries: [
			{ path: "alpha.md", heading: "Alpha", lines: 3 },
			{ path: "beta.txt", heading: "Indented", lines: 2 },
			{ path: "delta.txt", heading: null, lines: 2 },
			{ path: "gamma.md", heading: "Later", lines: 3 },
		],
	});
	assert.equal(headingOf("no hash here\n"), null);
	assert.equal(headingOf("### Three\n"), "Three");
});

test("the checker reports every way a result can be wrong", () => {
	const expected = { index_version: "0-spike",
	                   entries: [{ path: "a.md", heading: "A", lines: 1 }] };
	assert.deepEqual(diffIndex(expected, expected), []);
	assert.match(diffIndex({ index_version: "1", entries: expected.entries }, expected)[0],
		/index_version/);
	assert.match(diffIndex({ index_version: "0-spike", entries: [] }, expected)[0],
		/entries has 0 items/);
	assert.match(diffIndex({ index_version: "0-spike",
		entries: [{ path: "a.md", heading: "A", lines: 2 }] }, expected)[0],
		/entries\[0\].lines is 2, expected 1/);
	// A plausible extra field is a mismatch, not a bonus.
	assert.match(diffIndex({ index_version: "0-spike",
		entries: [{ path: "a.md", heading: "A", lines: 1, confidence: 0.9 }] }, expected)[0],
		/undeclared field "confidence"/);
});

test("a mount must declare ro or rw explicitly", () => {
	const spec = { name: "n", user: "1000:1000", network: "bridge", workdir: "/w",
	               image: "i", command: ["node"], mounts: [] };
	assert.match(runArgv({ ...spec, mounts: [{ source: "/a", target: "/b", mode: "ro" }] })
		.join(" "), /type=bind,source=\/a,target=\/b,readonly/);
	assert.throws(() => runArgv({ ...spec,
		mounts: [{ source: "/a", target: "/b", mode: "readonly" }] }), ContainerError);
});

test("no container spec may expose Baton state", () => {
	// Sources are REAL directories: since round 2 the fence
	// canonicalizes every mount source, so an unresolvable path is
	// refused as ambiguous rather than compared as a string.
	const deployment = scratch();
	const forbidden = join(deployment, "baton");
	mkdirSync(join(forbidden, "v11"), { recursive: true });
	const adapter = scratch();
	const credentials = scratch();
	const base = { name: "n", readOnlyRootfs: true,
	               mounts: [{ source: adapter, target: "/opt/acp", mode: "ro" },
	                        { source: credentials, target: "/run/claude-config", mode: "rw" }] };
	assert.doesNotThrow(() => assertNoBatonCapability(base, [forbidden]));
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: join(forbidden, "v11"), target: "/b", mode: "ro" }] },
		[forbidden]), /exposes Baton state/);
	// A parent of the forbidden path is just as fatal as the path.
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: deployment, target: "/h", mode: "ro" }] },
		[forbidden]), /exposes Baton state/);
	// A forbidden root that does not exist on this host is still
	// compared literally rather than dropped from the fence.
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: adapter, target: "/t", mode: "ro" }] },
		[adapter, "/nonexistent/baton"]), /exposes Baton state/);
});

test("the pre-claim posture is enforced clause by clause", () => {
	const base = { name: "n", readOnlyRootfs: true,
	               mounts: [{ source: "/opt/acp", target: "/opt/acp", mode: "ro" },
	                        { source: "/run/claude-config", target: "/run/claude-config", mode: "rw" },
	                        { source: "/offer", target: "/offer", mode: "ro" }] };
	assert.doesNotThrow(() => assertPreClaimPosture(base, "plan"));
	// A writable result destination.
	assert.throws(() => assertPreClaimPosture({ ...base,
		mounts: [...base.mounts, { source: "/o", target: "/out", mode: "rw" }] }, "plan"),
		/touches no Job input and no declared output/);
	// Even a READ-ONLY view of the Job's data: consent is decided from
	// the offer, not from the payload.
	assert.throws(() => assertPreClaimPosture({ ...base,
		mounts: [...base.mounts, { source: "/i", target: "/in", mode: "ro" }] }, "plan"),
		/never from the Job's data/);
	assert.throws(() => assertPreClaimPosture({ ...base, readOnlyRootfs: false }, "plan"),
		/writable root filesystem/);
	// The posture that review caught: consent running with full tool access.
	assert.throws(() => assertPreClaimPosture(base, "bypassPermissions"),
		/only 'plan' is accepted here/);
	// And the real spec builder satisfies all of it.
	const spec = preClaimSpec({ image: "i", user: "1000:1000", network: "bridge",
		acp_adapter: "/opt/acp", acp_entrypoint: "e.js" },
		{ credentials: "/c", offer: "/o" }, "a1");
	assert.doesNotThrow(() => assertPreClaimPosture(spec, "plan"));
	assert.equal(spec.readOnlyRootfs, true);
});

test("credential staging refuses a token too short-lived to survive an attempt", () => {
	const root = scratch();
	const source = join(root, "cred.json");
	const paths = { credentials: join(root, "staged") };
	const now = () => 1_000_000;
	writeFileSync(source, JSON.stringify({ claudeAiOauth: { expiresAt: 1_000_000 + 60_000 } }));
	assert.throws(() => stageCredentials(paths, { source, minRemainingMs: 900_000, now }),
		(error) => error instanceof RuntimeError && /rotate the operator's own refresh token/.test(error.message));
	writeFileSync(source, JSON.stringify({ claudeAiOauth: { expiresAt: 1_000_000 + 3_600_000 } }));
	const staged = stageCredentials(paths, { source, minRemainingMs: 900_000, now });
	assert.equal(staged.remaining_ms, 3_600_000);
	assert.match(readFileSync(join(paths.credentials, ".claude.json"), "utf8"),
		/hasCompletedOnboarding/);
	// A credential whose lifetime cannot be read is refused rather than assumed.
	writeFileSync(source, JSON.stringify({ claudeAiOauth: {} }));
	assert.throws(() => stageCredentials(paths, { source, minRemainingMs: 0, now }),
		/whose lifetime it cannot check/);
});

test("the reply parser takes the last fenced block and refuses prose", () => {
	assert.deepEqual(parseFencedJson('thinking\n```json\n{"a":1}\n```\nbut actually\n```json\n{"a":2}\n```'),
		{ a: 2 });
	assert.throws(() => parseFencedJson("I accept, and I am working on it."), ReplyError);
	assert.throws(() => parseFencedJson("```json\nnot json\n```"), /is not JSON/);
});

test("a recorded payload cannot overwrite the trace's own ordering field", () => {
	const path = join(scratch(), "trace.jsonl");
	const trace = new Trace(path, { now: () => "T" });
	trace.record("baton.claim", { seq: 5, claimant: "poc.claude" });
	trace.record("next", {});
	const lines = readFileSync(path, "utf8").trim().split("\n").map((line) => JSON.parse(line));
	assert.equal(lines[0].seq, 1);
	assert.equal(lines[0].detail.seq, 5);
	assert.equal(lines[1].seq, 2);
});

test("redaction hides secrets by name and by shape, but not the negative proof's subject", () => {
	const out = redact({
		token_fault: "replayed", jti: "abc", carried_token: true,
		token: "zzz", nested: { accessToken: "s3cret-value" },
		value: "eyJhbGciOiJIUzI1NiJ9.c2lnbmF0dXJlc2lnbmF0dXJl",
	});
	assert.equal(out.token_fault, "replayed");
	assert.equal(out.jti, "abc");
	assert.equal(out.carried_token, true);
	assert.match(out.token, /redacted/);
	assert.match(out.nested.accessToken, /redacted/);
	assert.match(out.value, /redacted/);
});

test("the Baton client refuses to attach to a production coordination home", () => {
	assert.throws(() => new BatonClient({ binary: "/bin/true",
		config: "/home/sl/baton-v11.8835cd5/baton.json", participant: "poc.claude" }),
		(error) => error instanceof BatonError && /refuses to attach/.test(error.message));
	assert.doesNotThrow(() => new BatonClient({ binary: "/bin/true",
		config: "/tmp/disposable/baton.json", participant: "poc.claude" }));
});

test("a readiness envelope is revalidated rather than trusted", () => {
	const good = { protocol_version: 11, participant: "poc.claude",
	               authority_uuid: "u", result: { actionable: [] } };
	assert.equal(validateReadiness(good, "poc.claude"), good);
	assert.throws(() => validateReadiness({ ...good, protocol_version: 10 }, "poc.claude"),
		/protocol_version 10 is not 11/);
	assert.throws(() => validateReadiness(good, "poc.rev"), /is for "poc.claude", not poc.rev/);
	assert.throws(() => validateReadiness({ ...good,
		result: { actionable: [{ kind: "work" }] } }, "poc.claude"), /no action_key/);
});

test("a streamed secret is scrubbed fragment by fragment", () => {
	const path = join(scratch(), "trace.jsonl");
	const trace = new Trace(path, { now: () => "T" });
	const secret = "eyJqdGkiOiIzN2FiNGEzNjAzYzgxZDIyYTNmZjQ2ZWIifQ.iWKsiMHgvjsnF5JqcksEdqm";
	trace.addSecret(secret);
	// Exactly how a streamed ACP reply arrives: short chunks, none of
	// which is recognisable as a credential on its own.
	for (const chunk of ["  \"token\": \"eyJqdGkiOiIzN2FiNGEzNj",
	                     "AzYzgxZDIyYTNmZjQ2ZWIifQ.iWKsiMHgvjsnF5JqcksEdqm\","]) {
		trace.record("preclaim.activity", { channel: "message", text: chunk });
	}
	const text = readFileSync(path, "utf8");
	for (let start = 0; start + 16 <= secret.length; start += 4) {
		assert.ok(!text.includes(secret.slice(start, start + 16)),
			`a 16-character fragment of the secret survived at offset ${start}`);
	}
	assert.match(text, /redacted/);
});

test("the Handler is read as a participant address, not as an object", async () => {
	const { handlerAddress } = await import("../src/baton_cli.mjs");
	assert.equal(handlerAddress({ handler: null }), null);
	assert.equal(handlerAddress({}), null);
	assert.equal(handlerAddress({ handler: { team: "poc", member: "claude",
		participant: "poc.claude" } }), "poc.claude");
});

test("a token mismatch is described structurally, without either token", async () => {
	const { describeTokenMismatch } = await import("../src/claim_token.mjs");
	const expected = "aaaabbbbcccc.ddddeeeeffff";
	assert.deepEqual(describeTokenMismatch(expected, expected), {
		comparable: true, received_length: 25, expected_length: 25, segments_received: 2,
		body_matches: true, mac_matches: true, body_length_delta: 0, mac_length_delta: 0,
		first_difference_at: -1, received_has_whitespace: false,
	});
	const truncated = describeTokenMismatch("aaaabbbbcccc.dddd", expected);
	assert.equal(truncated.mac_matches, false);
	assert.equal(truncated.body_matches, true);
	assert.equal(truncated.mac_length_delta, -8);
	const wrapped = describeTokenMismatch("aaaabbbbcccc.\ndddd eeeeffff", expected);
	assert.equal(wrapped.received_has_whitespace, true);
	assert.equal(wrapped.first_difference_at, 13);
});

test("the agent-visible token is a short opaque handle, not a signed payload", () => {
	const issuer = new ClaimTokenIssuer();
	// Deliberately long, distinctive binding values. Asserting that a
	// 39-character token does not "contain" a 2-character string like
	// "W2" is a coin flip, not a test — this failed once by chance
	// before the values were made long enough to mean something.
	const { token, payload } = issuer.mint({
		work: "W2-distinctive-work-identifier",
		participant: "poc.distinctive-participant",
		runtimeAttempt: "distinctive-runtime-attempt-0001",
		offerDigest: "d0d0d0d0distinctive-offer-digest-value-0123456789abcdef",
	});
	// Short enough for a model to transcribe reliably. The 402-character
	// signed-payload form this replaced was miscopied in the wild.
	assert.ok(token.length <= 64, `the handle is ${token.length} characters`);
	// And it carries NO binding information: everything the manager
	// checks lives in the manager.
	for (const secret of [payload.work, payload.participant, payload.runtime_attempt,
	                      payload.offer_digest, payload.expires_at]) {
		assert.ok(!Buffer.from(token).toString("base64").includes(secret));
		assert.ok(!token.includes(secret));
	}
	assert.equal(issuer.validate(token, {
		work: payload.work, participant: payload.participant,
		runtime_attempt: payload.runtime_attempt }).jti, payload.jti);
});

test("a handle that is correct but padded with whitespace still consents", () => {
	const issuer = new ClaimTokenIssuer();
	const { token, payload } = issuer.mint(mintArgs);
	for (const padded of [` ${token}`, `${token}\n`, `\t ${token} \n`]) {
		const issuerCopy = new ClaimTokenIssuer({ secret: issuer.secret });
		issuerCopy.issued.set(payload.jti, { state: "issued", payload });
		assert.equal(issuerCopy.validate(padded, BINDING).jti, payload.jti);
	}
});

test("a handle whose tag is altered by one character is refused", () => {
	const issuer = new ClaimTokenIssuer();
	const { token } = issuer.mint(mintArgs);
	const [jti, tag] = token.split(".");
	const flipped = `${jti}.${tag[0] === "A" ? "B" : "A"}${tag.slice(1)}`;
	assert.throws(() => issuer.validate(flipped, BINDING), (error) => error.reason === "forged");
});

// ---------------------------------------------------------------------
// Regressions for review-2026-08-20T19-57-54Z.md. Each of these encodes
// a boundary the prototype claimed to hold and did not.
// ---------------------------------------------------------------------

test("R1: a fence that was not established is refused, not recorded", async () => {
	const { assertQuiesced, ContainerError } = await import("../src/container.mjs");
	const clean = { running: false, stopped_by: "self", exit_code: 0, oom_killed: false };
	assert.equal(assertQuiesced(clean, "the worker container"), clean);

	// The exact shape the manager used to turn into evidence and carry on.
	assert.throws(() => assertQuiesced({ error: "docker inspect failed", running: null }, "w"),
		(error) => error instanceof ContainerError && /could not be proven quiescent/.test(error.message));
	assert.throws(() => assertQuiesced(null, "w"), /could not be proven quiescent/);
	assert.throws(() => assertQuiesced({ ...clean, running: true }, "w"), /still running/);
	// A forced stop is not a clean end: it cannot be distinguished from a
	// kill in the middle of the worker writing its result.
	assert.throws(() => assertQuiesced({ ...clean, stopped_by: "manager", exit_code: 137 }, "w"),
		/indistinguishable from a kill mid-write/);
	assert.throws(() => assertQuiesced({ ...clean, exit_code: 1 }, "w"), /did not finish normally/);
	assert.throws(() => assertQuiesced({ ...clean, exit_code: 137, oom_killed: true }, "w"),
		/OOM-killed/);
});

test("R2: an input source may not escape its bound record", async () => {
	const { resolveInputSource, copyTreeStrict, InputSourceError } =
		await import("../src/input_source.mjs");
	const { symlinkSync: link, mkdirSync: mkdir, writeFileSync: write } = await import("node:fs");

	const outside = scratch();
	write(join(outside, "secret.txt"), "TOP SECRET");
	const record = scratch();
	mkdir(join(record, "input"));
	write(join(record, "input", "note.md"), "# Note\n");

	assert.equal(resolveInputSource(record, "input"), join(record, "input"));

	for (const [declared, pattern] of [
		["../elsewhere", /traverses outside/],
		["input/../../elsewhere", /traverses outside/],
		[outside, /is absolute/],
		["", /declares no input source/],
		["missing", /ENOENT|no such file/],
		["input/note.md", /is not a directory/],
	]) {
		assert.throws(() => resolveInputSource(record, declared),
			(error) => error instanceof InputSourceError && pattern.test(error.message),
			`${declared} must be refused`);
	}

	// The reviewer's reproduction: a record-LOCAL name that is really a
	// link to somewhere else entirely. Lexically it is beyond reproach.
	const escaping = scratch();
	link(outside, join(escaping, "input"));
	assert.throws(() => resolveInputSource(escaping, "input"),
		/is a symbolic link/);

	// And a link nested below an otherwise honest source root.
	const nested = scratch();
	mkdir(join(nested, "input"));
	write(join(nested, "input", "ok.md"), "# ok\n");
	link(join(outside, "secret.txt"), join(nested, "input", "leak.txt"));
	const source = resolveInputSource(nested, "input");
	assert.throws(() => copyTreeStrict(source, scratch()), /is a symbolic link/);

	// A plain tree still copies, and copies exactly.
	const dest = scratch();
	const copied = copyTreeStrict(resolveInputSource(record, "input"), dest);
	assert.equal(copied.entries, 1);
	assert.equal(readFileSync(join(dest, "note.md"), "utf8"), "# Note\n");
});

test("R2b: the escape the reviewer reproduced no longer materializes", async () => {
	const { resolveInputSource } = await import("../src/input_source.mjs");
	const { symlinkSync: link, writeFileSync: write } = await import("node:fs");
	const outside = scratch();
	write(join(outside, "secret.txt"), "TOP SECRET");
	const record = scratch();
	link(outside, join(record, "input"));
	// Previously: cpSync(..., {dereference: true}) produced a perfectly
	// valid manifest containing secret.txt. Now the descriptor never gets
	// as far as being copied.
	assert.throws(() => resolveInputSource(record, "input"), /symbolic link/);
});

test("R3: a declaration must name this assignment and exactly the offered outputs", async () => {
	const { declarationProblems } = await import("../src/manager.mjs");
	const assignment = { work: "W2" };
	const offered = [{ name: "note-index", type: "file", path: "/out/index.json" }];
	const good = { work: "W2", results: [...offered], summary: "done" };
	assert.deepEqual(declarationProblems(good, assignment, offered), []);

	// The exact declaration the reviewer showed being accepted.
	const reviewers = { work: "W999", results: [], summary: "nothing" };
	const problems = declarationProblems(reviewers, assignment, offered);
	assert.ok(problems.some((p) => /declares work "W999", not "W2"/.test(p)));
	assert.ok(problems.some((p) => /declares 0 result\(s\), but the offer declared 1/.test(p)));

	for (const [mutation, pattern] of [
		[{ results: [{ ...offered[0], name: "other" }] }, /result 0 name is "other"/],
		[{ results: [{ ...offered[0], type: "directory" }] }, /result 0 type is "directory"/],
		[{ results: [{ ...offered[0], path: "/out/elsewhere.json" }] }, /result 0 path is/],
		[{ results: [offered[0], offered[0]] }, /declares 2 result\(s\)/],
	]) {
		const found = declarationProblems({ ...good, ...mutation }, assignment, offered);
		assert.ok(found.some((p) => pattern.test(p)),
			`expected ${pattern} in ${JSON.stringify(found)}`);
	}
	// Duplicate names are caught even when the count happens to line up.
	assert.ok(declarationProblems({ ...good, results: [offered[0], offered[0]] },
		assignment, [offered[0], offered[0]]).some((p) => /same result name more than once/.test(p)));
});

test("R3b: an undeclared TOP-LEVEL result field is a mismatch too", () => {
	const expected = { index_version: "0-spike", entries: [] };
	// Previously returned [] — the same exactness rule was applied inside
	// entries but not at the top level.
	const problems = diffIndex({ index_version: "0-spike", entries: [], undeclared: true },
		expected);
	assert.ok(problems.some((p) => /undeclared top-level field "undeclared"/.test(p)));
	assert.deepEqual(diffIndex(expected, expected), []);
});

test("R5: a post-claim failure releases the claim, and says so when it cannot", async () => {
	const { Manager } = await import("../src/manager.mjs");
	const config = {
		baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
		         participant: "poc.claude", waitTimeoutSeconds: 0 },
		token: { ttl_ms: 1000 }, runtime: {}, review_endpoint: "poc.rview",
	};
	const path = join(scratch(), "trace.jsonl");

	const manager = new Manager(config);
	const calls = [];
	manager.baton.release = async (work, expect, reason) => {
		calls.push({ work, expect, reason });
		return { result: { released_claimant: expect } };
	};
	manager.baton.detail = async () => ({ result: { phase: "queued", handler: null,
		route: { endpoint: "poc.job" }, ready: true } });
	const attempt = { work: "W2", runtime_attempt: "a1", trace: new Trace(path, { now: () => "T" }) };
	await manager.compensate(attempt, new Error("worker exploded"));
	assert.equal(attempt.status, "compensated");
	assert.equal(calls[0].expect, "poc.claude");
	assert.match(calls[0].reason, /worker exploded/);
	const lines = readFileSync(path, "utf8").trim().split("\n").map((l) => JSON.parse(l));
	assert.equal(lines.at(-1).detail.phase, "queued");
	assert.equal(lines.at(-1).detail.handler, null);

	// If the release itself fails the attempt is STRANDED and must not be
	// reported as a clean end.
	const stuck = new Manager(config);
	stuck.baton.release = async () => { throw new Error("authority unreachable"); };
	const bad = { work: "W2", runtime_attempt: "a2",
	              trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
	await stuck.compensate(bad, new Error("worker exploded"));
	assert.equal(bad.status, "stranded");
	assert.match(bad.strandedBy, /authority unreachable/);
});

test("R4b: consent and execution may not share a permission posture", async () => {
	const { validateConfig } = await import("../src/config.mjs");
	const base = JSON.parse(readFileSync(new URL("../poc.json", import.meta.url), "utf8"));
	assert.doesNotThrow(() => validateConfig(base));
	assert.throws(() => validateConfig({ ...base,
		runtime: { ...base.runtime, preclaim_permission_mode: "bypassPermissions" } }),
		/a consent turn does not execute tools/);
	assert.throws(() => validateConfig({ ...base,
		runtime: { ...base.runtime, execution_permission_mode: "plan" } }),
		/consent and execution are not the same posture/);
});

// ---------------------------------------------------------------------
// Round-2 review regressions (review-2026-08-20T21-07-20Z.md). Each
// encodes an ordering or a fence the prototype claimed and did not have.
// ---------------------------------------------------------------------

test("R2-1: a turn without a manager deadline is refused outright", async () => {
	const { ContainerAcpSession } = await import("../src/acp_session.mjs");
	const spec = { name: "n", workdir: "/w", mounts: [] };
	for (const bad of [undefined, null, 0, -1, 1.5, "300000"]) {
		assert.throws(() => new ContainerAcpSession(spec, {
			permissionMode: "plan", promptTimeoutMs: bad }),
			/needs an explicit positive promptTimeoutMs/,
			`promptTimeoutMs=${JSON.stringify(bad)} must be refused`);
	}
	assert.doesNotThrow(() => new ContainerAcpSession(spec, {
		permissionMode: "plan", promptTimeoutMs: 1000 }));
});

test("R2-1: a silent agent turn times out instead of hanging forever", async () => {
	const { ContainerAcpSession, TurnTimeout } =
		await import("../src/acp_session.mjs");
	const session = new ContainerAcpSession(
		{ name: "v12poc-worker-silent", workdir: "/out", mounts: [] },
		{ permissionMode: "bypassPermissions", promptTimeoutMs: 40 });
	// A live container whose agent simply never answers: the promise
	// that used to be raced only against child death.
	session.connection = { prompt: () => new Promise(() => {}) };
	session.sessionId = "session-1";
	session.exited = new Promise(() => {});
	const started = Date.now();
	await assert.rejects(() => session.prompt("do the work"),
		(error) => error instanceof TurnTimeout
			&& /produced no result within 40ms/.test(error.message)
			&& /rather than holding the claim/.test(error.message));
	assert.ok(Date.now() - started < 5000, "it must not wait on the agent");
});

test("R2-1: a turn that answers in time is untouched by the deadline", async () => {
	const { ContainerAcpSession } = await import("../src/acp_session.mjs");
	const session = new ContainerAcpSession(
		{ name: "n", workdir: "/out", mounts: [] },
		{ permissionMode: "plan", promptTimeoutMs: 5000 });
	session.connection = { prompt: async () => ({ stopReason: "end_turn" }) };
	session.sessionId = "session-1";
	session.exited = new Promise(() => {});
	assert.deepEqual(await session.prompt("hello"), { stopReason: "end_turn" });
});

test("R2-2: removal is only proven by an explicit absence answer", async () => {
	const { removeAndVerify } = await import("../src/container.mjs");
	// A container that genuinely is not there.
	const gone = await removeAndVerify("v12poc-absent-by-construction");
	assert.equal(gone.gone, true);
});

test("R2-2: an unprovable reap withholds the release and strands the attempt",
	async () => {
		// THE ordering defect. A fence that could not be established used
		// to release the Work while the old execution container may still
		// have been running.
		const { Manager } = await import("../src/manager.mjs");
		const config = {
			baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: { state_dir: scratch() },
			review_endpoint: "poc.rview",
		};
		const manager = new Manager(config);
		const released = [];
		manager.baton.release = async (...args) => { released.push(args); return {
			result: { released_claimant: "poc.claude" } }; };
		manager.baton.detail = async () => ({ result: { phase: "queued",
			handler: null, route: { endpoint: "poc.job" }, ready: true } });
		manager.baton.wait = async () => ({ result: { actionable: [] } });
		// The attempt commits a claim and then fails; the worker cannot
		// be proven gone.
		manager.attempt = async (_action, attempt) => {
			attempt.claimCommitted = true;
			throw new Error("the fence could not be established");
		};
		const order = [];
		manager.reap = async () => { order.push("reap");
			return { gone: false, reason: "docker still resolves the container" }; };
		const original = manager.compensate.bind(manager);
		manager.compensate = async (...args) => { order.push("compensate");
			return original(...args); };

		const attempt = await manager.dispatch(
			{ local_id: "W2", work: "aaa-W2", action_key: "k" });
		assert.equal(attempt.status, "stranded");
		assert.match(attempt.strandedBy, /still resolves/);
		assert.deepEqual(released, [], "the claim must NOT be released");
		assert.deepEqual(order, ["reap"], "compensation must not even be attempted");
		const trace = readFileSync(attempt.paths.trace, "utf8");
		assert.match(trace, /compensation.withheld/);
		assert.match(trace, /not advertised as available/);
	});

test("R2-2: a proven reap releases, and reaping happens first", async () => {
	const { Manager } = await import("../src/manager.mjs");
	const config = {
		baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
		         participant: "poc.claude", waitTimeoutSeconds: 0 },
		token: { ttl_ms: 1000 }, runtime: { state_dir: scratch() },
		review_endpoint: "poc.rview",
	};
	const manager = new Manager(config);
	const order = [];
	manager.baton.release = async () => { order.push("release");
		return { result: { released_claimant: "poc.claude" } }; };
	manager.baton.detail = async () => ({ result: { phase: "queued",
		handler: null, route: { endpoint: "poc.job" }, ready: true } });
	manager.attempt = async (_action, attempt) => {
		attempt.claimCommitted = true;
		throw new Error("the worker exploded");
	};
	manager.reap = async () => { order.push("reap"); return { gone: true }; };
	const attempt = await manager.dispatch(
		{ local_id: "W2", work: "aaa-W2", action_key: "k" });
	assert.equal(attempt.status, "compensated");
	assert.deepEqual(order, ["reap", "release"],
		"the container must be proven gone BEFORE the Job is advertised again");
});

test("R2-3: a mount source that is a symlink to Baton state is refused", async () => {
	const { symlinkSync: link, mkdirSync: mkdir } = await import("node:fs");
	const forbiddenRoot = scratch();
	mkdir(join(forbiddenRoot, "authority"));
	const honest = scratch();
	const staging = scratch();
	link(join(forbiddenRoot, "authority"), join(staging, "adapter"));

	const forbidden = [join(forbiddenRoot, "authority")];
	// The reviewer's reproduction: lexically this source shares nothing
	// with the forbidden root, and Docker would resolve it anyway.
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: join(staging, "adapter"), target: "/opt/acp", mode: "ro" }] },
		forbidden), /exposes Baton state/);
	// The refusal names what it really is, so the operator is not left
	// comparing two strings that look unrelated.
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: join(staging, "adapter"), target: "/opt/acp", mode: "ro" }] },
		forbidden), /really /);
	// An honest source still passes.
	assert.doesNotThrow(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: honest, target: "/opt/acp", mode: "ro" }] }, forbidden));
	// Ambiguity is refused rather than resolved.
	assert.throws(() => assertNoBatonCapability({ name: "n",
		mounts: [{ source: join(staging, "missing"), target: "/t", mode: "ro" }] },
		forbidden), /cannot be resolved/);
});

test("R2-4: the declared result is the pinned DIRECTORY, with declared entries",
	async () => {
		const { declarationProblems } = await import("../src/manager.mjs");
		const assignment = { work: "W2" };
		const offered = [{ name: "note-index", type: "directory", path: "/out",
		                   entries: ["index.json"] }];
		// The agent restates identity, not the containment rule.
		assert.deepEqual(declarationProblems({ work: "W2", summary: "done",
			results: [{ name: "note-index", type: "directory", path: "/out" }] },
			assignment, offered), []);
		// The type the finding pinned is enforced: a file is not a
		// directory, and the two are not treated as equivalent.
		const asFile = declarationProblems({ work: "W2", summary: "done",
			results: [{ name: "note-index", type: "file", path: "/out/index.json" }] },
			assignment, offered);
		assert.ok(asFile.some((problem) => /type is "file"/.test(problem)));
		assert.ok(asFile.some((problem) => /path is "\/out\/index.json"/.test(problem)));
	});

test("R2-4: an undeclared file inside the result directory is refused", () => {
	const root = scratch();
	writeFileSync(join(root, "index.json"), "{}");
	assert.doesNotThrow(() => assertContained(manifestOf(root), ["index.json"]));
	writeFileSync(join(root, "notes.tmp"), "scratch");
	assert.throws(() => assertContained(manifestOf(root), ["index.json"]),
		/contains "notes.tmp", which the Job did not declare/);
});

// ---------------------------------------------------------------------
// Round-3 review regressions (review-2026-08-20T23-30-47Z.md).
// ---------------------------------------------------------------------

test("R3-1: the staged credential is disposed once containers are absent",
	async () => {
		const { disposeCredentials, stageCredentials } =
			await import("../src/runtime.mjs");
		const root = scratch();
		const source = join(root, "cred.json");
		const paths = { credentials: join(root, "staged") };
		const now = () => 1_000_000;
		writeFileSync(source, JSON.stringify({
			claudeAiOauth: { expiresAt: 1_000_000 + 3_600_000,
				refreshToken: "sk-ant-refresh-DO-NOT-RETAIN" } }));
		stageCredentials(paths, { source, minRemainingMs: 0, now });
		const staged = join(paths.credentials, ".credentials.json");
		assert.ok(readFileSync(staged, "utf8").includes("DO-NOT-RETAIN"));

		const disposal = disposeCredentials(paths);
		assert.equal(disposal.disposed, true);
		assert.ok(!existsSync(paths.credentials),
			"the staged credential directory must be gone");
		// Disposing what is already gone is not an error.
		assert.deepEqual(disposeCredentials(paths), { disposed: false, reason: "absent" });
	});

test("R3-1: every attempt path disposes, and an unprovable reap retains loudly",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const { stageCredentials } = await import("../src/runtime.mjs");
		const make = () => {
			const state = scratch();
			const config = {
				baton: { binary: "/bin/true", config: join(state, "baton.json"),
				         participant: "poc.claude", waitTimeoutSeconds: 0 },
				token: { ttl_ms: 1000 }, runtime: { state_dir: state },
				review_endpoint: "poc.rview",
			};
			return { config, state };
		};
		const credentialSource = join(scratch(), "cred.json");
		writeFileSync(credentialSource, JSON.stringify({
			claudeAiOauth: { expiresAt: 9_999_999_999_999,
				refreshToken: "sk-ant-refresh-DO-NOT-RETAIN" } }));

		// (a) containers proven gone -> disposed, on the failure path.
		{
			const { config } = make();
			const manager = new Manager(config);
			manager.attempt = async (_a, attempt) => {
				stageCredentials(attempt.paths, { source: credentialSource,
					minRemainingMs: 0 });
				throw new Error("pre-claim failure");
			};
			const attempt = await manager.dispatch(
				{ local_id: "W2", work: "aaa-W2", action_key: "k" });
			assert.equal(attempt.credentialsDisposed, true);
			assert.ok(!existsSync(attempt.paths.credentials));
			assert.match(readFileSync(attempt.paths.trace, "utf8"),
				/credential.disposed/);
		}
		// (b) a container that mounts it cannot be proven gone -> the
		//     secret is RETAINED and named, never quietly assumed gone.
		{
			const { config } = make();
			const manager = new Manager(config);
			manager.attempt = async (_a, attempt) => {
				stageCredentials(attempt.paths, { source: credentialSource,
					minRemainingMs: 0 });
				attempt.claimCommitted = true;
				throw new Error("worker fence could not be established");
			};
			// The unprovable case, stubbed at the reap boundary: what is
			// under test is what the manager DOES with it.
			manager.reap = async (attempt) => {
				attempt.credentialsDisposed = false;
				attempt.retainedSecret = attempt.paths.credentials;
				attempt.trace.record("credential.retained",
					{ path: attempt.paths.credentials });
				return { gone: false, reason: "docker still resolves the container" };
			};
			const attempt = await manager.dispatch(
				{ local_id: "W2", work: "aaa-W2", action_key: "k" });
			assert.equal(attempt.status, "stranded");
			assert.equal(attempt.credentialsDisposed, false);
			assert.equal(attempt.retainedSecret, attempt.paths.credentials);
			const trace = readFileSync(attempt.paths.trace, "utf8");
			assert.match(trace, /credential.retained/);
			assert.match(trace, /retained_credential/);
		}
	});

test("R3-2: the guard refuses the live alias and links into production",
	async () => {
		const { isProductionAuthority } = await import("../src/baton_cli.mjs");
		// The exact path the deployment is conventionally addressed by,
		// which the previous pattern accepted because it required a dot.
		assert.equal(isProductionAuthority("/home/sl/baton-v11/baton.json"), true);
		assert.equal(isProductionAuthority("/home/sl/baton-v11.8835cd5/baton.json"), true);
		// A home that does not exist yet cannot be resolved and must
		// still be refused.
		assert.equal(isProductionAuthority("/home/sl/baton-v11.deadbeef/baton.json"), true);
		assert.equal(isProductionAuthority("/home/sl/.config/baton/acp/baton.json"), true);
		// A link that RESOLVES into production, which a lexical check
		// walked straight past.
		if (existsSync("/home/sl/baton-v11.8835cd5")) {
			const staging = scratch();
			symlinkSync("/home/sl/baton-v11.8835cd5", join(staging, "sneaky"));
			assert.equal(isProductionAuthority(join(staging, "sneaky", "baton.json")),
				true, "a symlink into a production home must be refused");
		}
		// And a disposable authority must still pass. The second path is
		// this prototype's own, which the in-repository migration moved
		// out of the retired external root and under the explicit
		// external state root.
		assert.equal(isProductionAuthority("/tmp/disposable/baton.json"), false);
		assert.equal(
			isProductionAuthority("/tmp/baton-v12-poc/authority/baton.json"),
			false);
	});

test("R3-3: a committed mutation whose result was lost is reconciled", async () => {
	const { Manager } = await import("../src/manager.mjs");
	const config = {
		baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
		         participant: "poc.claude", waitTimeoutSeconds: 0 },
		token: { ttl_ms: 1000 }, runtime: { state_dir: scratch() },
		review_endpoint: "poc.rview",
	};
	const manager = new Manager(config);
	const trace = new Trace(join(scratch(), "trace.jsonl"), { now: () => "T" });

	// The claim committed; both the call and its replay lost the result.
	manager.baton.detail = async () => ({ result: {
		phase: "active", handler: { participant: "poc.claude" },
		route: { endpoint: "poc.job" }, last_change_seq: 42 } });
	const claimed = await manager.committed(
		async () => { throw new Error("timed out"); }, "W2", "claim",
		(state) => state.handler?.participant === "poc.claude",
		(state) => ({ result: { claimant: state.handler.participant,
			phase: state.phase, seq: state.last_change_seq, reconciled: true } }),
		trace);
	assert.equal(claimed.result.claimant, "poc.claude");
	assert.equal(claimed.result.reconciled, true);
	assert.match(readFileSync(trace.path, "utf8"), /baton.claim.reconciled/);

	// The effect is genuinely absent: the failure stands.
	manager.baton.detail = async () => ({ result: {
		phase: "queued", handler: null, route: { endpoint: "poc.job" },
		last_change_seq: 7 } });
	await assert.rejects(() => manager.committed(
		async () => { throw new Error("timed out"); }, "W2", "claim",
		(state) => state.handler?.participant === "poc.claude",
		() => ({}), trace), /timed out/);

	// A retry that replays the committed result never reaches the projection.
	let calls = 0;
	const replayed = await manager.committed(async () => {
		calls += 1;
		if (calls === 1) throw new Error("lost output");
		return { result: { claimant: "poc.claude", seq: 9 } };
	}, "W2", "claim", () => false, () => ({}), trace);
	assert.equal(replayed.result.seq, 9);
	assert.equal(calls, 2);
});

test("R3-3: a committed pass whose result was lost is not called stranded",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const config = {
			baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: { state_dir: scratch() },
			review_endpoint: "poc.rview",
		};
		const manager = new Manager(config);
		const trace = new Trace(join(scratch(), "trace.jsonl"), { now: () => "T" });
		// The Job reached review; only the response was lost.
		manager.baton.detail = async () => ({ result: {
			phase: "queued", handler: null,
			route: { endpoint: "poc.rview" }, last_change_seq: 51 } });
		const handoff = await manager.committed(
			async () => { throw new Error("timed out"); }, "W2", "pass",
			(state) => state.route.endpoint === "poc.rview"
				&& state.handler === null,
			(state) => ({ result: { to: state.route.endpoint,
				destination_phase: state.phase, reconciled: true } }),
			trace);
		assert.equal(handoff.result.to, "poc.rview");
		assert.equal(handoff.result.reconciled, true);
	});

test("R3-4: the container is launched with the canonical source, not the alias",
	async () => {
		const { runArgv } = await import("../src/container.mjs");
		const real = scratch();
		const staging = scratch();
		symlinkSync(real, join(staging, "adapter"));
		const spec = { name: "n", user: "1000:1000", network: "bridge",
			workdir: "/w", image: "i", command: ["node"],
			mounts: [{ source: join(staging, "adapter"), target: "/opt/acp",
			           mode: "ro" }] };
		const checked = assertNoBatonCapability(spec, ["/home/sl/opt/baton"]);
		const argv = runArgv(checked).join(" ");
		assert.ok(!argv.includes(join(staging, "adapter")),
			"the mutable alias must not reach docker run");
		assert.ok(argv.includes(real),
			"the validated canonical source must be what is launched");
		// The alias is retained for evidence, so a reader can still see
		// what the configuration named.
		assert.equal(checked.mounts[0].alias, join(staging, "adapter"));
	});

// ---------------------------------------------------------------------
// Round-4 review regressions (review-2026-08-20T23-56-14Z.md).
// ---------------------------------------------------------------------

test("R4-1: a retained credential cannot be reported as a clean return",
	async () => {
		// The path the review found: the WORKER is proven gone, the
		// consent container is not, so the credential correctly stays —
		// and the attempt still finished as `returned`, exit zero, with
		// the only trace of it inside the attempt journal.
		const { Manager } = await import("../src/manager.mjs");
		const { stageCredentials } = await import("../src/runtime.mjs");
		const state = scratch();
		const config = {
			baton: { binary: "/bin/true", config: join(state, "baton.json"),
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: { state_dir: state },
			review_endpoint: "poc.rview",
		};
		const source = join(scratch(), "cred.json");
		writeFileSync(source, JSON.stringify({
			claudeAiOauth: { expiresAt: 9_999_999_999_999,
				refreshToken: "sk-ant-refresh-DO-NOT-RETAIN" } }));

		const manager = new Manager(config);
		manager.attempt = async (_action, attempt) => {
			stageCredentials(attempt.paths, { source, minRemainingMs: 0 });
			// The worker is gone; the consent container is not.
			attempt.credentialsDisposed = false;
			attempt.retainedSecret = attempt.paths.credentials;
			attempt.uncleanReason =
				`a staged credential remains at ${attempt.paths.credentials}`;
			attempt.handedOff = true;
		};
		manager.reap = async (attempt) => ({ gone: true, clean: false,
			reason: attempt.uncleanReason });
		const attempt = await manager.dispatch(
			{ local_id: "W2", work: "aaa-W2", action_key: "k" });

		assert.equal(attempt.status, "returned-unclean",
			"a retained credential must not be reported as `returned`");
		assert.notEqual(attempt.status, "returned");
		assert.equal(attempt.credentialsDisposed, false);
		assert.match(attempt.retainedSecret, /claude-config$/);
		// And the secret really is still there, so the report is honest.
		assert.ok(existsSync(join(attempt.retainedSecret, ".credentials.json")));
	});

test("R4-1: reap reports worker absence and cleanliness as separate facts",
	async () => {
		// `gone` gates compensation; `clean` gates calling it a success.
		// Collapsing them is what let a retained credential ride out on a
		// clean return.
		const { Manager } = await import("../src/manager.mjs");
		const state = scratch();
		const manager = new Manager({
			baton: { binary: "/bin/true", config: join(state, "baton.json"),
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: { state_dir: state },
			review_endpoint: "poc.rview" });
		const attempt = { runtimeAttempt: "a1", runtime_attempt: "a1",
			paths: attemptPathsFor(state, "a1"),
			trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
		const reaped = await manager.reap(attempt);
		// Nothing was ever launched, so both containers are absent and
		// there is no credential staged: clean.
		assert.equal(reaped.gone, true);
		assert.equal(reaped.clean, true);
		assert.equal(reaped.reason, null);
	});

test("R4-2: an ambiguous committed release is reconciled, not called stranded",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const config = {
			baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: { state_dir: scratch() },
			review_endpoint: "poc.rview",
		};
		// The release COMMITTED and its result was lost: the Handler is
		// already gone and the Job is available again.
		const manager = new Manager(config);
		let releases = 0;
		manager.baton.release = async () => { releases += 1; throw new Error("timed out"); };
		manager.baton.detail = async () => ({ result: { phase: "queued",
			handler: null, route: { endpoint: "poc.job" }, ready: true } });
		const attempt = { work: "W2", runtime_attempt: "a1",
			trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
		await manager.compensate(attempt, new Error("worker exploded"));
		assert.equal(attempt.status, "compensated",
			"a committed release whose result was lost is not stranding");
		assert.equal(releases, 2, "the operation id is replayed before reconciling");
		const trace = readFileSync(attempt.trace.path, "utf8");
		assert.match(trace, /baton.release.reconciled/);

		// And when the Handler really is still held, it strands.
		const stuck = new Manager(config);
		stuck.baton.release = async () => { throw new Error("timed out"); };
		stuck.baton.detail = async () => ({ result: { phase: "active",
			handler: { participant: "poc.claude" },
			route: { endpoint: "poc.job" }, ready: false } });
		const held = { work: "W2", runtime_attempt: "a2",
			trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
		await stuck.compensate(held, new Error("worker exploded"));
		assert.equal(held.status, "stranded");
	});

test("R4-2: every manager mutation carries an operation identity", async () => {
	const { BatonClient } = await import("../src/baton_cli.mjs");
	const client = new BatonClient({ binary: "/bin/true",
		config: "/tmp/disposable/baton.json", participant: "poc.claude" });
	const seen = [];
	client.run = async (verb, operands) => { seen.push([verb, operands]); return { result: {} }; };
	await client.claim("W2", "op-claim");
	await client.pass("W2", "poc.rview", "comment", "op-pass");
	await client.release("W2", "poc.claude", "reason", "op-release");
	await client.say("T2", "recap", [], "op-say");
	for (const [verb, operands] of seen) {
		assert.ok(operands.some((operand) => operand.startsWith("op-id=")),
			`${verb} must carry an operation identity`);
	}
});

test("R4-3: the capability fence refuses the live checkout and coordination alias",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const manager = new Manager({
			baton: { binary: "/bin/true", config: "/tmp/disposable/baton.json",
			         participant: "poc.claude", waitTimeoutSeconds: 0 },
			token: { ttl_ms: 1000 }, runtime: {}, review_endpoint: "poc.rview" });
		const forbidden = manager.forbiddenPaths();
		// The finding forbids runtime mounts back into the checkout, and
		// this fence did not name it — the proof only caught such a mount
		// after the worker had already run.
		assert.ok(forbidden.includes("/home/sl/src/baton"));
		assert.ok(forbidden.includes("/home/sl/baton-v11"));

		if (!existsSync("/home/sl/src/baton")) return;
		// A DIRECT mount of the checkout is refused before launch.
		assert.throws(() => assertNoBatonCapability({ name: "n",
			mounts: [{ source: "/home/sl/src/baton", target: "/opt/acp", mode: "ro" }] },
			forbidden), /exposes Baton state/);
		// And so is a symlink resolving into it.
		const staging = scratch();
		symlinkSync("/home/sl/src/baton", join(staging, "adapter"));
		assert.throws(() => assertNoBatonCapability({ name: "n",
			mounts: [{ source: join(staging, "adapter"), target: "/opt/acp", mode: "ro" }] },
			forbidden), /exposes Baton state/);
		// An honest adapter tree still passes.
		assert.doesNotThrow(() => assertNoBatonCapability({ name: "n",
			mounts: [{ source: scratch(), target: "/opt/acp", mode: "ro" }] }, forbidden));
	});

// ---------------------------------------------------------------------
// Round-5 review regressions (review-2026-08-21T00-38-29Z.md).
// ---------------------------------------------------------------------

function stubManager(overrides = {}) {
	const state = scratch();
	return {
		baton: { binary: "/bin/true", config: join(state, "baton.json"),
		         participant: "poc.claude", waitTimeoutSeconds: 0 },
		token: { ttl_ms: 1000 }, runtime: { state_dir: state },
		review_endpoint: "poc.rview", ...overrides };
}

test("R5-1: a committed recap is replayed, not re-executed as new Work",
	async () => {
		// The defect: `say` carried an operation id that nobody replayed.
		// A recap that committed and lost its result threw before the
		// pass, the outer catch compensated an already-complete
		// assignment, and the Job went back on the queue for a SECOND
		// execution with a duplicate recap to follow.
		const { Manager } = await import("../src/manager.mjs");
		const manager = new Manager(stubManager());
		const trace = new Trace(join(scratch(), "t.jsonl"), { now: () => "T" });
		const recap = "isolated ACP worker completed W2";

		let attempts = 0;
		const said = await manager.committed(
			async () => { attempts += 1; throw new Error("lost output"); },
			"W2", "say",
			(messages) => messages.some((message) => message.body === recap),
			() => ({ result: { reconciled: true } }), trace,
			// The authority says the recap is there.
			async () => [{ seq: 9, body: recap }]);
		assert.equal(said.result.reconciled, true,
			"a committed recap must be recognised, not retried into a failure");
		assert.equal(attempts, 2, "the operation id is replayed before reconciling");
		assert.match(readFileSync(trace.path, "utf8"), /baton.say.reconciled/);

		// And when the recap genuinely is absent, the failure stands —
		// this must not become a blanket "assume it worked".
		await assert.rejects(() => manager.committed(
			async () => { throw new Error("lost output"); }, "W2", "say",
			(messages) => messages.some((message) => message.body === recap),
			() => ({}), trace, async () => []), /lost output/);
	});

test("R5-1: a recap that never committed does not silently pass as sent",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const manager = new Manager(stubManager());
		const trace = new Trace(join(scratch(), "t.jsonl"), { now: () => "T" });
		// A DIFFERENT message is in the thread: not this recap.
		await assert.rejects(() => manager.committed(
			async () => { throw new Error("lost output"); }, "W2", "say",
			(messages) => messages.some((message) => message.body === "the recap"),
			() => ({}), trace,
			async () => [{ seq: 1, body: "somebody else's message" }]),
			/lost output/);
		assert.match(readFileSync(trace.path, "utf8"), /baton.say.not-committed/);
	});

test("R5-2: an immediate successor claim does not make a committed pass look failed",
	async () => {
		// After the pass commits, the DESTINATION may be claimed before
		// the fallback read. Requiring a null Handler turned that
		// legitimate successor into evidence that the handoff had not
		// happened.
		const { Manager } = await import("../src/manager.mjs");
		const manager = new Manager(stubManager());
		const trace = new Trace(join(scratch(), "t.jsonl"), { now: () => "T" });
		const settled = (state) => state.route.endpoint === "poc.rview"
			&& (state.handler?.participant ?? null) !== "poc.claude";

		for (const successor of [null, "poc.rev", "poc.someone-else"]) {
			const handoff = await manager.committed(
				async () => { throw new Error("timed out"); }, "W2", "pass",
				settled,
				(state) => ({ result: { to: state.route.endpoint,
					successor: state.handler?.participant ?? null, reconciled: true } }),
				trace,
				async () => ({ route: { endpoint: "poc.rview" }, phase: "queued",
					handler: successor ? { participant: successor } : null }));
			assert.equal(handoff.result.reconciled, true,
				`a successor of ${successor} must not undo a committed pass`);
		}
		// Still at the source route and still held by us: genuinely not passed.
		await assert.rejects(() => manager.committed(
			async () => { throw new Error("timed out"); }, "W2", "pass",
			settled, () => ({}), trace,
			async () => ({ route: { endpoint: "poc.job" }, phase: "active",
				handler: { participant: "poc.claude" } })), /timed out/);
	});

test("R5-2: an immediate successor claim does not make a committed release look failed",
	async () => {
		const { Manager } = await import("../src/manager.mjs");
		const config = stubManager();
		const manager = new Manager(config);
		// The release committed and the next eligible member claimed it
		// before the fallback read.
		manager.baton.release = async () => { throw new Error("timed out"); };
		manager.baton.detail = async () => ({ result: { phase: "active",
			handler: { participant: "poc.gemini" },
			route: { endpoint: "poc.job" }, ready: false } });
		const attempt = { work: "W2", runtime_attempt: "a1",
			trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
		await manager.compensate(attempt, new Error("worker exploded"));
		assert.equal(attempt.status, "compensated",
			"a successor Handler proves this participant's claim is gone");
		assert.match(readFileSync(attempt.trace.path, "utf8"), /baton.release.reconciled/);

		// Still held by US: genuinely not released.
		const stuck = new Manager(config);
		stuck.baton.release = async () => { throw new Error("timed out"); };
		stuck.baton.detail = async () => ({ result: { phase: "active",
			handler: { participant: "poc.claude" },
			route: { endpoint: "poc.job" }, ready: false } });
		const held = { work: "W2", runtime_attempt: "a2",
			trace: new Trace(join(scratch(), "t.jsonl"), { now: () => "T" }) };
		await stuck.compensate(held, new Error("worker exploded"));
		assert.equal(held.status, "stranded");
	});
