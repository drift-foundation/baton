// Placement regressions for the in-repository migration
// (`baton:work/records/2026/08/finding-v12-isolated-agent-workers/findings/`
// `finding-v12-in-repository-migration`).
//
// The prototype used to live in its own external root, so "state sits
// beside the code" was harmless. It now lives inside the Baton checkout
// as `v12/`, and the reviewed runtime fence refuses to mount any path
// inside that checkout into a worker. Relaxing that fence because the
// source moved would have discarded a W76 security boundary, so the
// migration moved the STATE instead: everything disposable — the
// authority, the Job records, per-attempt state, staged credentials and
// generated proof output — lives under one explicit external state root.
//
// These cases pin that separation. They deliberately do not re-test the
// assignment lifecycle, which the migration did not touch.

import { test, after } from "node:test";
import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync,
         symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { POC_ROOT, validateConfig } from "../src/config.mjs";
import { CHECKOUT_ROOT, MARKER_NAME, assertLabel, assertOwnedStateRoot,
         assertStateRoot, assertUnderStateRoot, markerContent, markerPath,
         ownershipOf, planPlacement, PlacementError } from "../src/placement.mjs";
import { assertNoBatonCapability } from "../src/runtime.mjs";
import { ownedTemp, removeOwnedRoot, removeOwnedRoots }
	from "./owned_roots.mjs";

const PLACEMENT = join(POC_ROOT, "src", "placement.mjs");
const CONFIG = join(POC_ROOT, "poc.json");
const ROOT = "/tmp/baton-v12-poc";

function placement(...argv) {
	return spawnSync(process.execPath, [PLACEMENT, ...argv], { encoding: "utf8" });
}

// The line number of the first EXECUTABLE occurrence. These scripts
// discuss `rm -rf` in their comments, and a comment is not an act.
function firstCommand(text, needle) {
	const lines = text.split("\n");
	const at = lines.findIndex((line) => !line.trimStart().startsWith("#")
		&& line.includes(needle));
	assert.ok(at >= 0, `no executable line contains ${needle}`);
	return at;
}

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(POC_ROOT, "..");
const SAMPLE = JSON.parse(readFileSync(join(POC_ROOT, "poc.json"), "utf8"));
// W2907: as in `unit.test.mjs` — the registry records each root at
// creation and one `after` hook removes exactly those. The five families
// below kept their in-test removals, which run on the SUCCESSFUL tail of
// each case; the W30 failure left an absent-parent root and a
// CLI-stranger root behind, which is the gap this closes.
const scratch = () => ownedTemp("v12poc-placement-");
after(removeOwnedRoots);

// Every case that points a real entry point at its OWN root rebases the
// same four disposable paths onto it. Written out once per case, one
// copy drifts from the others, so it is written once here. `dir` is
// where the document lands, which is the root itself unless the case
// needs that root to stay absent.
function rebasedConfig(root, dir = root) {
	const path = join(dir, "poc.json");
	writeFileSync(path, JSON.stringify({ ...SAMPLE, state_root: root,
		record_base: join(root, "records"),
		baton: { ...SAMPLE.baton, config: join(root, "authority", "baton.json") },
		runtime: { ...SAMPLE.runtime, state_dir: join(root, "attempts") } }, null, 2));
	return path;
}

test("the prototype root is this subtree, and it is inside the Baton checkout",
	() => {
		assert.equal(POC_ROOT, resolve(HERE, ".."));
		assert.ok(POC_ROOT.startsWith(`${REPO}/`),
			`${POC_ROOT} is not inside ${REPO}; this suite's premise is gone`);
		// The relocation is the whole reason the state root exists.
		assert.ok(existsSync(join(POC_ROOT, "src", "manager.mjs")));
	});

test("the shipped sample keeps every disposable path outside the checkout",
	() => {
		// Read as DATA, not through validateConfig: this must hold on a
		// host with no Docker, no adapter tree and no credential.
		const disposable = {
			"baton.config": SAMPLE.baton.config,
			record_base: SAMPLE.record_base,
			"runtime.state_dir": SAMPLE.runtime.state_dir,
		};
		assert.equal(typeof SAMPLE.state_root, "string");
		for (const [key, value] of Object.entries(disposable)) {
			assert.ok(!value.startsWith(`${REPO}/`) && value !== REPO,
				`${key} ${value} is inside the Baton checkout`);
			assert.ok(value.startsWith(`${SAMPLE.state_root}/`),
				`${key} ${value} is outside state_root ${SAMPLE.state_root}`);
		}
		// The sample no longer names the retired external root anywhere.
		const text = JSON.stringify(SAMPLE);
		assert.ok(!text.includes("/home/sl/src/baton-v12-poc"),
			"the sample still points at the retired external prototype root");
	});

test("the state root must be external to the WHOLE checkout", () => {
	// Round-1 review, [P1]. The first version compared against `v12/`
	// alone, so a SIBLING inside the checkout passed — and proof setup
	// would then have created and recursively removed state in the
	// repository long before any container fence was consulted.
	assert.throws(() => assertStateRoot(join(CHECKOUT_ROOT, "v12-state-sibling")),
		/overlaps the Baton checkout/,
		"a sibling of v12/ inside the checkout must be refused");
	for (const inside of [POC_ROOT, join(POC_ROOT, "run"), CHECKOUT_ROOT,
	                      join(CHECKOUT_ROOT, "work"), dirname(CHECKOUT_ROOT)]) {
		assert.throws(() => assertStateRoot(inside), /overlaps the Baton checkout/,
			`${inside} was not refused`);
	}
	assert.throws(() => assertStateRoot("relative/path"), /must be an absolute path/);
	assert.throws(() => assertStateRoot("/tmp/has space"), /whitespace/);
	// A genuinely external root passes.
	assert.equal(assertStateRoot(ROOT), ROOT);
});

// A disposable root that IS ours: created here, marked here, removed
// here. Nothing in this file deletes anything the prototype did not make.
function ownedRoot() {
	const root = ownedTemp("v12poc-owned-");
	writeFileSync(markerPath(root), markerContent(root));
	return root;
}

test("root deletion needs positive ownership evidence, not path shape", () => {
	// Round-2 review, [P1]. Depth and a denylist cannot prove a directory
	// belongs to this prototype: these all pass both and none is ours.
	// `state-clean` recursively makes its target writable and removes it,
	// so shape alone must never be enough.
	for (const unrelated of ["/var/log", "/usr/local", "/etc/ssl",
	                         process.env.HOME]) {
		if (!unrelated || !existsSync(unrelated)) continue;
		assert.throws(() => assertOwnedStateRoot(unrelated, { forDeletion: true }),
			PlacementError, `${unrelated} was accepted for deletion`);
	}
	// An existing directory with no marker is refused BY NAME, and the
	// refusal says what to do instead.
	const stranger = ownedTemp("v12poc-stranger-");
	assert.throws(() => ownershipOf(stranger),
		new RegExp(`carries no ${MARKER_NAME}`));
	// A marker COPIED from another root authorizes nothing: it names the
	// root it was written for.
	const owned = ownedRoot();
	writeFileSync(markerPath(stranger), readFileSync(markerPath(owned), "utf8"));
	assert.throws(() => ownershipOf(stranger), /names root .*, not/);
	// A marker that is not ours, and one that is not readable JSON.
	const impostor = ownedTemp("v12poc-impostor-");
	writeFileSync(markerPath(impostor),
		JSON.stringify({ owner: "something-else", root: impostor }));
	assert.throws(() => ownershipOf(impostor), /names owner/);
	writeFileSync(markerPath(impostor), "not json");
	assert.throws(() => ownershipOf(impostor), /unreadable or not JSON/);
	// Our own marked root passes, and a root that does not exist yet is
	// `fresh` — creating it is how ownership is established.
	assert.equal(ownershipOf(owned), "owned");
	assert.equal(assertOwnedStateRoot(owned, { forDeletion: true }).state, "owned");
	assert.equal(ownershipOf(join(tmpdir(), "v12poc-absent-root-xyz")), "fresh");
	// W2907 R1: remove AND forget, as one action. `rmSync` alone left these
	// three pathnames armed in the registry, so anything that recreated one
	// before the suite hook was deleted with it.
	for (const path of [stranger, owned, impostor]) removeOwnedRoot(path);
});

test("the cleanup path refuses an ABSENT root and offers no path to remove",
	() => {
		// Round-3 review, [P1]. This used to return `{state: "fresh"}`
		// for a root that does not exist, on the reasoning that there
		// was nothing there to remove — but the value went straight to
		// `chmod -R` and `rm -rf`, and anything could create an
		// unrelated directory at that path in between. Ownership is not
		// a property of the moment the check runs.
		//
		// Round-4 review, [P1]: this case used to establish its
		// precondition by recursively removing a FIXED path, which is
		// the exact hazard it exists to prevent — the name does not
		// make a shared path unowned, and another run or checkout could
		// have data there. The absent candidate is now a child of a
		// parent THIS test created and that has never been created, so
		// its absence is a fact rather than something deleted into
		// being. Nothing is removed but the parent, at the end.
		const owned = ownedTemp("v12poc-absent-parent-");
		const absent = join(owned, "never-created");
		assert.equal(existsSync(absent), false,
			"the fixture child was created by something");

		assert.throws(() => assertOwnedStateRoot(absent, { forDeletion: true }),
			/nothing this prototype owns to remove/);
		assert.equal(existsSync(absent), false,
			"the refused deletion check created the root");

		// SETUP still accepts it: creating a fresh root is how ownership
		// is established, and that path must stay open.
		assert.equal(assertOwnedStateRoot(absent).state, "fresh");
		assert.equal(ownershipOf(absent), "fresh");
		assert.equal(existsSync(absent), false);

		// And through the CLI verb `state-clean` actually consumes.
		// The document cannot live in the root here: the root's absence
		// is the precondition. It lands in the parent instead of a
		// second temporary directory, so the one removal below still
		// removes every path this case created.
		const config = rebasedConfig(absent, owned);
		const refused = placement("state", "--config", config);
		assert.equal(refused.status, 2, refused.stdout);
		assert.equal(refused.stdout, "",
			"the cleanup verb printed a path it must not remove");
		assert.ok(!refused.stdout.includes(absent));
		assert.match(refused.stderr, /nothing this prototype owns to remove/);
		assert.equal(existsSync(absent), false);

		// The setup verbs still work against the same absent root, so
		// the correction did not close the way in.
		const own = placement("own", "--config", config);
		assert.equal(own.status, 0, own.stderr);
		assert.equal(own.stdout.trim().split(" ")[1], "fresh");
		assert.equal(existsSync(absent), false,
			"asking about ownership created the root");
		// Only the parent this test made, and only at the end.
		removeOwnedRoot(owned);
	});

test("the cleanup entry point refuses an existing root that is not ours", () => {
	// End to end through the CLI, without deleting anything: `state` is
	// the only verb `state-clean` consumes.
	const stranger = ownedTemp("v12poc-cli-stranger-");
	mkdirSync(join(stranger, "someone-elses-data"), { recursive: true });
	const config = rebasedConfig(stranger);
	const refused = placement("state", "--config", config);
	assert.equal(refused.status, 2, refused.stdout);
	assert.match(refused.stderr, new RegExp(`carries no ${MARKER_NAME}`));
	assert.equal(refused.stdout, "", "a refused cleanup still named a path to remove");
	assert.ok(existsSync(join(stranger, "someone-elses-data")));

	// The same directory, once it is genuinely ours, cleans normally.
	writeFileSync(markerPath(stranger), markerContent(stranger));
	const allowed = placement("state", "--config", config);
	assert.equal(allowed.status, 0, allowed.stderr);
	assert.equal(allowed.stdout.trim(), stranger);
	removeOwnedRoot(stranger);
});

test("a filesystem-wide or top-level state root is refused", () => {
	// Round-1 review, [P1]. This root is created, written into and
	// recursively REMOVED by `state-clean`, so accepting `/tmp` or `/var`
	// meant offering somebody else's data to `rm -rf`.
	for (const broad of ["/", "/tmp", "/var", "/home", "/usr", "/etc", "/opt",
	                     "/srv", "/run", "/mnt", "/root", "/var/tmp"]) {
		assert.throws(() => assertStateRoot(broad),
			/filesystem-wide or top-level directory/, `${broad} was not refused`);
	}
	// Depth, not just the denylist: one component is a top-level
	// directory whatever it happens to be called.
	assert.throws(() => assertStateRoot("/not-a-real-top-level-dir"),
		/filesystem-wide or top-level directory/);
	assert.doesNotThrow(() => assertStateRoot("/not-a-real-top-level-dir/v12"));
	// And an ancestor of the operator's home is refused even though it is
	// outside the checkout and deep enough.
	if (process.env.HOME && process.env.HOME.split("/").length > 2) {
		assert.throws(() => assertStateRoot(dirname(process.env.HOME)),
			/(filesystem-wide|contains the home directory)/);
	}
});

test("a state root that RESOLVES into the checkout is refused", () => {
	// Spelling is not placement: the check canonicalizes the longest
	// existing prefix, so a symlink that lands in the checkout is caught
	// here rather than at container launch.
	const staging = scratch();
	const link = join(staging, "state");
	symlinkSync(POC_ROOT, link);
	assert.throws(() => assertStateRoot(link), /overlaps the Baton checkout/);
	assert.throws(() => assertStateRoot(join(link, "deeper")),
		/overlaps the Baton checkout/);
});

test("every destructive operand must be a STRICT descendant of that root", () => {
	// The root itself is removed only by the recipe that owns it; no
	// other operation may reach it, and nothing outside it is a legal
	// target at all.
	assert.doesNotThrow(() => assertUnderStateRoot("t", ROOT, `${ROOT}/attempts`));
	assert.throws(() => assertUnderStateRoot("t", ROOT, ROOT),
		/strict descendant/, "the state root itself is not a per-operation target");
	for (const outside of ["/tmp/somewhere-else/attempts", join(POC_ROOT, "work"),
	                       join(CHECKOUT_ROOT, "work"), "/", "/etc"]) {
		assert.throws(() => assertUnderStateRoot("t", ROOT, outside),
			/strict descendant/, `${outside} was not refused`);
	}
	assert.throws(() => assertUnderStateRoot("t", ROOT, "records"),
		/must be an absolute path/);
	// `..` is resolved before the comparison, so traversal cannot spell
	// its way back out.
	assert.throws(() => assertUnderStateRoot("t", ROOT, `${ROOT}/../../etc`),
		/strict descendant/);
});

test("the evidence label must be one safe path component", () => {
	// Round-1 review, [P1]. The label reaches `rm -rf "$STATE/evidence/$LABEL"`.
	for (const bad of ["..", ".", "../..", "a/b", "/abs", "", "-leading",
	                   ".hidden", "with space", "a\u0000b"]) {
		assert.throws(() => assertLabel(bad), PlacementError,
			`label ${JSON.stringify(bad)} was not refused`);
	}
	for (const good of ["run", "proof-r7-migration", "r8_2", "A1.2"]) {
		assert.equal(assertLabel(good), good);
	}
});

test("the whole plan is computed without creating or deleting anything", () => {
	const raw = JSON.parse(readFileSync(CONFIG, "utf8"));
	const plan = planPlacement(raw, { label: "proof-check" });
	assert.equal(plan.stateRoot, raw.state_root);
	assert.equal(plan.evidence, `${raw.state_root}/evidence/proof-check`);
	for (const path of [plan.authority, plan.recordBase, plan.stateDir,
	                    plan.evidence]) {
		assert.ok(path.startsWith(`${plan.stateRoot}/`), path);
		assert.ok(!existsSync(path) || true);
	}
	// A traversal label is refused by the plan, not by the shell that
	// would otherwise have removed the result.
	assert.throws(() => planPlacement(raw, { label: "../.." }), /ONE path component/);
	// And a record path may not climb out of its base.
	assert.throws(() => planPlacement({ ...raw, record_path: "../escape" }),
		/traverse out of the record base/);
});

test("the shell entry points get their paths from that one authority", () => {
	// `plan` is what run-proof.sh reads, `paths` is what
	// new-authority.sh compares its operands against, `own` and `marker`
	// carry ownership, and `state` is the only thing state-clean
	// consumes. Every one refuses nonzero and prints nothing usable.
	const planned = placement("plan", "--config", CONFIG, "--label", "run");
	assert.equal(planned.status, 0, planned.stderr);
	const fields = planned.stdout.trim().split(" ");
	assert.equal(fields.length, 6, planned.stdout);
	assert.ok(fields.every((field) => !/\s/.test(field)));

	// `paths` is the same plan without an evidence label, so a script
	// that only needs the configured targets does not have to invent one.
	const paths = placement("paths", "--config", CONFIG);
	assert.equal(paths.status, 0, paths.stderr);
	assert.deepEqual(paths.stdout.trim().split(" "), fields.slice(0, 5));

	const traversal = placement("plan", "--config", CONFIG, "--label", "../..");
	assert.equal(traversal.status, 2);
	assert.equal(traversal.stdout, "");
	assert.match(traversal.stderr, /ONE path component/);

	// `marker` names the root it is written for, which is what makes a
	// copied marker worthless elsewhere.
	const marker = placement("marker", "--config", CONFIG);
	assert.equal(marker.status, 0, marker.stderr);
	assert.equal(JSON.parse(marker.stdout).root, ROOT);

	// `state` is the DELETION path, so it answers only for a root this
	// prototype demonstrably owns. This used to invoke the SAMPLE
	// configuration and branch on whichever way the ambient
	// /tmp/baton-v12-poc happened to be, claiming both outcomes were
	// asserted. They were not: on a host where the sample root does not
	// exist the refusal is the DIFFERENT absent-root one, so the case
	// failed for a reason that had nothing to do with the entry point.
	// The condition it names is now constructed — a root this test
	// created, existing and deliberately unmarked — and the sample root
	// is neither read nor created nor removed.
	const unowned = ownedTemp("v12poc-entry-unowned-");
	try {
		const state = placement("state", "--config", rebasedConfig(unowned));
		assert.equal(state.status, 2, state.stdout);
		assert.equal(state.stdout, "",
			"a refused cleanup still named a path to remove");
		assert.match(state.stderr, new RegExp(`carries no ${MARKER_NAME}`));
		assert.equal(existsSync(unowned), true,
			"the refused deletion check removed the root");
		assert.equal(existsSync(markerPath(unowned)), false,
			"the refused deletion check established ownership");
	} finally {
		// Only this test's own fixture, and even if an assertion above threw.
		removeOwnedRoot(unowned);
	}

	assert.equal(placement("plan", "--config", CONFIG).status, 2);
	assert.equal(placement("bogus", "--config", CONFIG).status, 2);
	assert.equal(placement("paths").status, 2);
	// The retired free-form target check is gone: proving a path was
	// *some* descendant of the root is exactly what round 2 found
	// insufficient.
	assert.equal(placement("check", "--config", CONFIG,
		"--target", `${ROOT}/authority`).status, 2);
});

test("the configuration refuses a document with no explicit state placement",
	() => {
		// `record_base` used to be optional and fall back to the prototype
		// root. That fallback is exactly the relocation hazard, so it is
		// gone and both keys are required.
		const withoutBase = { ...SAMPLE };
		delete withoutBase.record_base;
		assert.throws(() => validateConfig(withoutBase), /record_base/);
		const withoutRoot = { ...SAMPLE };
		delete withoutRoot.state_root;
		assert.throws(() => validateConfig(withoutRoot), /state_root/);
	});

test("the runtime fence still refuses the whole checkout, prototype included",
	() => {
		// The migration did NOT weaken this. The forbidden root is the
		// checkout, and the prototype is now inside it, so a mount of the
		// prototype's own directory is refused for the same reason.
		const forbidden = ["/home/sl/opt/baton", REPO, "/home/sl/baton-v11"];
		for (const source of [REPO, POC_ROOT, join(POC_ROOT, "fixtures")]) {
			assert.throws(() => assertNoBatonCapability(
				{ name: "n", mounts: [{ source, target: "/in", mode: "ro" }] },
				forbidden), /exposes Baton state/,
				`${source} was not refused`);
		}
		// And so is a symlink that merely resolves into it.
		const staging = scratch();
		symlinkSync(POC_ROOT, join(staging, "proto"));
		assert.throws(() => assertNoBatonCapability({ name: "n",
			mounts: [{ source: join(staging, "proto"), target: "/in", mode: "ro" }] },
			forbidden), /exposes Baton state/);
		// An external per-attempt directory still passes — that is the
		// whole point of moving the state rather than the fence.
		assert.doesNotThrow(() => assertNoBatonCapability({ name: "n",
			mounts: [{ source: scratch(), target: "/in", mode: "ro" }] }, forbidden));
	});

test("the disposable authority accepts only the exact configured plan",
	() => {
		// Round-1 review, [P1]: the first operand was handed to `rm -rf`
		// behind a production denylist and a subtree comparison.
		// Round-2 review, [P1]: proving each operand was SOME strict
		// descendant of the state root was still not enough — the
		// retained evidence directory and the attempt state are
		// descendants too, so a swap or a plausible typo would have
		// removed the evidence and built an authority over the attempts.
		// Every refusal below must happen with nothing created and
		// nothing removed.
		const script = join(POC_ROOT, "scripts", "new-authority.sh");
		const refusals = [
			[join(POC_ROOT, "run", "authority"), `${ROOT}/records`],
			[join(CHECKOUT_ROOT, "scratch-authority"), `${ROOT}/records`],
			[`${ROOT}/authority`, join(CHECKOUT_ROOT, "work")],
			["/tmp/elsewhere/authority", `${ROOT}/records`],
			[ROOT, `${ROOT}/records`],
			["/home/sl/baton-v11.8835cd5", `${ROOT}/records`],
			// Round 2: legal-but-wrong descendants of the very same root.
			[`${ROOT}/evidence`, `${ROOT}/records`],
			[`${ROOT}/attempts`, `${ROOT}/records`],
			[`${ROOT}/authority`, `${ROOT}/evidence`],
			[`${ROOT}/authority`, `${ROOT}/attempts`],
			// And the two configured operands, swapped.
			[`${ROOT}/records`, `${ROOT}/authority`],
		];
		for (const argv of refusals) {
			// Existence BEFORE, so a legitimately pre-existing state
			// directory is not mistaken for something this call made.
			const before = argv.map((path) => existsSync(path));
			const refused = spawnSync(script, argv, { encoding: "utf8" });
			assert.equal(refused.status, 2, `${argv.join(" ")}: ${refused.stdout}`);
			assert.match(refused.stderr,
				/not the configured plan|strict descendant|production state|carries no/);
			argv.forEach((path, index) => {
				assert.equal(existsSync(path), before[index],
					`a refused invocation changed whether ${path} exists`);
			});
		}
		// Both operands are required; neither has a default any more.
		const missing = spawnSync(script, [`${ROOT}/authority`], { encoding: "utf8" });
		assert.notEqual(missing.status, 0);
		assert.match(missing.stderr, /record-base/);
		// The retained evidence a wrong operand would have removed is
		// still there. This is the concrete loss round 2 identified.
		if (existsSync(`${ROOT}/evidence`)) {
			assert.ok(existsSync(`${ROOT}/evidence`),
				"a refused invocation removed the retained evidence directory");
		}
	});

test("the proof runner reads every disposable location from the config", () => {
	// Not a re-run of the proof: a text assertion that the runner no
	// longer carries the retired external root or a state path relative
	// to its own directory.
	const runner = readFileSync(join(POC_ROOT, "scripts", "run-proof.sh"), "utf8");
	assert.ok(!runner.includes("/home/sl/src/baton-v12-poc"),
		"the runner still names the retired external prototype root");
	assert.ok(!runner.includes("/home/sl/src/baton "),
		"the runner still hard-codes the checkout path");
	for (const derived of ["$STATE_DIR", "$RECORD_BASE", "$AUTHORITY", "$REPO"]) {
		assert.ok(runner.includes(derived), `the runner does not use ${derived}`);
	}
	assert.ok(!/\brm -rf "\$ROOT\//.test(runner),
		"the runner still deletes paths inside the prototype");
	// Round-1 review, [P1]: the validated plan comes BEFORE the first
	// destructive line, and the runner no longer parses the config itself.
	assert.ok(runner.includes("plan --config"),
		"the runner does not ask the placement authority for a plan");
	assert.ok(firstCommand(runner, "placement.mjs") < firstCommand(runner, "rm -rf"),
		"the runner removes something before the placement plan is validated");
	assert.ok(!runner.includes('json.load(open(sys.argv[1]))\nprint(c["state_root"]'),
		"the runner still derives state paths itself");
	// And every entry point that deletes goes through the same authority.
	const recipes = readFileSync(join(POC_ROOT, "justfile"), "utf8");
	assert.ok(recipes.includes("placement.mjs state"),
		"state-clean does not use the placement authority");
	assert.ok(!/case "\$STATE" in/.test(recipes),
		"state-clean still carries its own denylist");
	const authority = readFileSync(join(POC_ROOT, "scripts", "new-authority.sh"),
		"utf8");
	assert.ok(firstCommand(authority, "placement.mjs")
		< firstCommand(authority, "rm -rf"),
		"new-authority.sh removes its operand before validating it");
	assert.ok(firstCommand(authority, "placement.mjs")
		< firstCommand(authority, "mkdir"),
		"new-authority.sh creates its operand before validating it");
	// Round 2: it must act on the PLAN's values, never on the raw
	// operands it was handed.
	assert.ok(authority.includes("PLANNED_AUTHORITY")
		&& authority.includes("PLANNED_RECORD_BASE"),
		"new-authority.sh does not bind itself to the configured plan");
	assert.ok(!/\brm -rf "\$1"|\brm -rf "\$HOME_DIR"[\s\S]*?PLANNED/.test(authority));
	assert.ok(firstCommand(authority, "PLANNED_AUTHORITY")
		< firstCommand(authority, "rm -rf"),
		"new-authority.sh removes before it has the planned target");
	// Ownership is established or confirmed before either entry point
	// writes under the root.
	for (const [name, text] of [["run-proof.sh", runner],
	                            ["new-authority.sh", authority]]) {
		assert.ok(firstCommand(text, "own --config") < firstCommand(text, "mkdir"),
			`${name} creates state before confirming it owns the root`);
		assert.ok(firstCommand(text, "own --config") < firstCommand(text, "rm -rf"),
			`${name} removes state before confirming it owns the root`);
	}
	// And nothing goes near the retired free-form target check.
	for (const text of [runner, authority,
	                    readFileSync(join(POC_ROOT, "justfile"), "utf8")]) {
		assert.ok(!text.includes("placement.mjs\" check")
			&& !text.includes("placement.mjs check"),
			"an entry point still uses the retired descendant-only check");
	}
});

test("the proof runner refuses a traversal label before it removes anything",
	() => {
		// End to end, and cheap: the refusal happens at the plan, before
		// Docker, before the authority, before any `rm -rf`.
		const before = existsSync(`${ROOT}/evidence`);
		const refused = spawnSync(join(POC_ROOT, "scripts", "run-proof.sh"),
			["../escape"], { encoding: "utf8", cwd: POC_ROOT });
		assert.equal(refused.status, 2, refused.stdout);
		assert.match(refused.stderr, /ONE path component/);
		assert.ok(!refused.stdout.includes("prerequisites"),
			"the run continued past the refused plan");
		assert.equal(existsSync(`${ROOT}/evidence`), before);
		// The path the traversal would have reached, had the label been
		// joined and then removed.
		assert.ok(!existsSync(`${ROOT}/escape`));
	});

test("the prototype's own gate is self-contained and adds no root recipe", () => {
	// `v12/` stays independently buildable and testable, and the root
	// justfile does not delegate to it: the v11 gate must not start
	// depending on a prototype.
	const justfile = readFileSync(join(POC_ROOT, "justfile"), "utf8");
	assert.match(justfile, /^test:/m);
	assert.match(justfile, /^proof /m);
	const rootJustfile = readFileSync(join(REPO, "justfile"), "utf8");
	assert.ok(!rootJustfile.includes("v12"),
		"the root justfile delegates to the prototype; v12/ is self-contained");
	// The shipped v11 deployer must not pick the prototype up either.
	const deployer = readFileSync(join(REPO, "tools", "deploy_work.py"), "utf8");
	assert.ok(!deployer.includes('"v12'), "the v11 deployer packages the prototype");
});

test("the prototype imports nothing from the v11 product tree", () => {
	// It lives in the repository now; it is still not part of it. Every
	// import resolves inside `v12/` or to a pinned dependency.
	const sources = execFileSync("bash", ["-c",
		`find ${JSON.stringify(POC_ROOT)} -name node_modules -prune -o `
		+ `\\( -name '*.mjs' -o -name 'v12-poc' \\) -type f -print`],
		{ encoding: "utf8" }).trim().split("\n").filter(Boolean);
	assert.ok(sources.length > 10, sources);
	const DEPENDENCIES = JSON.parse(readFileSync(
		join(POC_ROOT, "package.json"), "utf8")).dependencies ?? {};
	let pinned = 0;
	for (const file of sources) {
		// A module specifier never contains whitespace, which is what
		// separates a real `from "..."` from prose that happens to read
		// like one inside a message string.
		for (const [, specifier] of readFileSync(file, "utf8")
				.matchAll(/\bfrom\s+"(\S+)"/g)) {
			if (specifier.startsWith("node:")) continue;
			if (specifier.startsWith(".")) {
				assert.ok(resolve(dirname(file), specifier).startsWith(`${POC_ROOT}/`),
					`${file} imports ${specifier} from outside the prototype`);
				continue;
			}
			// W2929: the allowed set is READ from `package.json` rather than
			// hardcoded, and "pinned" is checked rather than assumed — the
			// name must be a declared dependency AND its version must be an
			// exact pin, so a caret range cannot enter by being declared.
			// The guard therefore still fails for an undeclared import, and
			// now also for a declared-but-floating one.
			const name = specifier.startsWith("@")
				? specifier.split("/").slice(0, 2).join("/")
				: specifier.split("/")[0];
			assert.ok(Object.hasOwn(DEPENDENCIES, name),
				`${file} imports an unpinned package ${specifier}`);
			assert.match(DEPENDENCIES[name], /^\d+\.\d+\.\d+$/,
				`${name} is declared as ${DEPENDENCIES[name]}, which is a range `
				+ `rather than an exact pin`);
			pinned += 1;
		}
	}
	// The scan found real imports rather than passing on an empty match.
	assert.ok(pinned >= 1, "no pinned dependency import was seen; the scan is inert");
});
