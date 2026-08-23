// W2907: the fixture-root registry, and the failure path it exists for.
//
// `baton:work/records/2026/08/finding-v12-test-fixture-audit-follow-up/`,
// the explicit follow-up to the cancelled W30.
//
// The audit's finding was not "cleanup is missing" but something
// narrower and worse: the cleanup that DID exist ran on the successful
// tail of each test, so an assertion failure leaked every root that case
// had made. One isolated run left 162 `v12poc-test-*` roots, and the
// failing W30 invocation left a `v12poc-absent-parent-*` and a
// `v12poc-cli-stranger-*` root behind.
//
// A regression for that cannot be a passing test. It has to run a test
// file that genuinely fails, which is why `fixtures/fixture_cleanup_probe.mjs`
// exists outside the `*.test.mjs` glob and is spawned from here.
//
// The two properties under test are opposites and both matter: the roots
// this suite created must be GONE, and everything it merely linked to
// must be UNTOUCHED.

import { test, after } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync,
         rmSync, symlinkSync, unlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { ownedRoots, ownedTemp, ownsRoot, removeOwnedRoot, removeOwnedRoots,
         retireOwnedRoot } from "./owned_roots.mjs";

after(removeOwnedRoots);

const PROBE = join(dirname(fileURLToPath(import.meta.url)), "fixtures",
                   "fixture_cleanup_probe.mjs");

// Every test-owned family this suite creates. Written out rather than
// derived, so a family added without a cleanup boundary shows up here as
// a case somebody has to think about. The audit of 2026-08-21 found
// eight; `v12-authority-` is the ninth, added by W2928, and
// `v12-manager-` the tenth, added by W2929.
const FAMILIES = [
	"v12poc-test-", "v12poc-placement-", "v12poc-owned-", "v12poc-stranger-",
	"v12poc-impostor-", "v12poc-absent-parent-", "v12poc-cli-stranger-",
	"v12poc-entry-unowned-", "v12-authority-", "v12-manager-",
];

// One probe run, inside a blast radius this regression owns.
//
// Review 2026-08-22 [P1]: this used to scrape `W2907-ROOTS` out of the
// child test runner's stdout, which is a channel the runner's reporter and
// isolation settings own. Under the default isolation on a supported Node
// the probe file's own stdout is hidden behind the file-level result, so
// both cases failed with "the probe reported no roots" — and a DENIED
// spawn looked identical, because nothing here diagnosed spawn error,
// signal or empty output. The report is now a file this parent names, and
// every other way the child can fail is a distinct named outcome.
function runProbe(mode) {
	// The child's roots land under a parent WE made, so "did anything
	// survive" is an exact inventory of one directory rather than a scan of
	// the host's temporary directory.
	const sandbox = ownedTemp("v12poc-test-");
	// The external target lives OUTSIDE that sandbox on purpose: if it were
	// inside, its survival would prove nothing about following links,
	// because the sandbox is not removed either.
	const external = ownedTemp("v12poc-placement-");
	writeFileSync(join(external, "precious.txt"), "PRECIOUS");
	mkdirSync(join(external, "subdir"), { recursive: true });
	writeFileSync(join(external, "subdir", "deep.txt"), "DEEP");
	const report = join(sandbox, "probe-report.json");

	// NODE_TEST_CONTEXT is deleted deliberately. It is set in this process,
	// the child inherits it, and `node --test` then refuses to run files
	// "recursively" — reporting success while executing nothing.
	const env = { ...process.env, TMPDIR: sandbox, W2907_MODE: mode,
	              W2907_TARGET: external, W2907_REPORT: report };
	delete env.NODE_TEST_CONTEXT;
	const proc = spawnSync(process.execPath, ["--test", PROBE],
		{ encoding: "utf8", env });

	// Every way this can go wrong, named. A regression that cannot tell a
	// denied spawn from a clean run is not evidence about cleanup.
	const detail = `exit=${proc.status} signal=${proc.signal ?? "none"}\n`
		+ `stdout:\n${proc.stdout}\nstderr:\n${proc.stderr}`;
	assert.equal(proc.error, undefined,
		`the probe could not be spawned: ${proc.error?.message}\n${detail}`);
	assert.equal(proc.signal, null, `the probe was killed by a signal\n${detail}`);
	assert.ok(existsSync(report),
		`the probe wrote no report file\n${detail}`);
	let state;
	try {
		state = JSON.parse(readFileSync(report, "utf8"));
	} catch (error) {
		throw new Error(`the probe's report is malformed (${error.message})\n`
			+ `raw: ${readFileSync(report, "utf8").slice(0, 400)}\n${detail}`);
	}
	// Report COMPLETENESS, separately from what it says: all three tests ran.
	assert.deepEqual(state.tests, ["creates", "intended-failure", "after-failure"],
		`the probe did not run all three of its tests\n${detail}`);
	assert.equal(state.mode, mode, detail);
	assert.ok(Array.isArray(state.roots) && state.roots.length >= 4,
		`the probe reported ${state.roots?.length} roots\n${detail}`);
	return { proc, external, sandbox, roots: state.roots, state, detail };
}

function assertNoResidue({ roots, sandbox, external, detail }) {
	for (const root of roots) {
		assert.equal(existsSync(root), false, `${root} survived the probe\n${detail}`);
	}
	// And nothing of ANY test-owned family is left in the sandbox — which
	// catches a root the probe made but did not report.
	const survivors = readdirSync(sandbox)
		.filter((entry) => FAMILIES.some((prefix) => entry.startsWith(prefix)));
	assert.deepEqual(survivors, [],
		`test-owned roots survived in the sandbox: ${survivors.join(", ")}`);
	// The external target the probe linked to is untouched: still there,
	// still its own bytes, still its subtree.
	assert.equal(readFileSync(join(external, "precious.txt"), "utf8"), "PRECIOUS");
	assert.equal(readFileSync(join(external, "subdir", "deep.txt"), "utf8"), "DEEP");
}

test("W2907: a PASSING run leaves no fixture root and no touched target", () => {
	const result = runProbe("pass");
	assert.equal(result.proc.status, 0, `the probe should have passed\n${result.detail}`);
	assert.equal(result.state.reachedIntendedFailure, false);
	assertNoResidue(result);
});

test("W2907: a FAILING run leaves no fixture root either", () => {
	// The case W30 actually hit. Before the correction this is where the
	// roots were left behind, because cleanup lived on the successful tail
	// of each test.
	const result = runProbe("fail");
	assert.notEqual(result.proc.status, 0,
		`the probe was supposed to fail\n${result.detail}`);
	// It failed for ITS reason. The flag is written immediately before the
	// intended assertion, so "reached it and died there" is distinguishable
	// from "died somewhere else" WITHOUT depending on the runner's output.
	assert.equal(result.state.reachedIntendedFailure, true,
		`the probe never reached its intended failure\n${result.detail}`);
	// Including the root created AFTER the failing test.
	assert.ok(result.roots.length >= 4, result.roots);
	assertNoResidue(result);
});

test("W2907: recreating a removed root's pathname survives suite cleanup", () => {
	// Review 2026-08-22 [P1]. The registry recorded a pathname, and six
	// placement families remove their roots in their own tails, so once a
	// test deleted a root the suite owned nothing at that name — yet the
	// hook stayed armed on it. The reviewer recreated the pathname with a
	// replacement marker and the hook deleted the replacement: the exact
	// path-identity ABA that `placement.mjs` spends four cases refusing.
	const root = ownedTemp("v12poc-test-");
	assert.equal(ownsRoot(root), true);
	// The tail removal, as the placement cases now do it: remove AND forget.
	removeOwnedRoot(root);
	assert.equal(existsSync(root), false);
	assert.equal(ownsRoot(root), false, "the registry stayed armed on a dead pathname");

	// Somebody else takes the pathname over.
	mkdirSync(root, { recursive: true });
	writeFileSync(join(root, "replacement-owner.txt"), "NOT OURS");
	removeOwnedRoots();
	assert.equal(existsSync(join(root, "replacement-owner.txt")), true,
		"suite cleanup deleted a replacement owner's data");
	rmSync(root, { recursive: true, force: true });

	// The same holds for a root the PRODUCT path removed: retiring it needs
	// the positively observed absence that justifies retiring it.
	const byProduct = ownedTemp("v12poc-placement-");
	assert.throws(() => retireOwnedRoot(byProduct, { observedAbsent: true }),
		/still exists; it cannot be retired/);
	rmSync(byProduct, { recursive: true, force: true });
	retireOwnedRoot(byProduct, { observedAbsent: true });
	assert.equal(ownsRoot(byProduct), false);
	assert.throws(() => retireOwnedRoot(byProduct, { observedAbsent: true }),
		/not a registered fixture root/);
});

test("W2907: a pathname that is no longer our directory is left alone", () => {
	// The second line, behind remove-and-forget: identity is recorded at
	// creation and re-checked immediately before removal, so a name that now
	// resolves to a different directory is refused rather than removed.
	const root = ownedTemp("v12poc-impostor-");
	writeFileSync(join(root, "ours.txt"), "OURS");
	rmSync(root, { recursive: true, force: true });
	mkdirSync(root, { recursive: true });
	writeFileSync(join(root, "theirs.txt"), "THEIRS");
	assert.throws(() => removeOwnedRoot(root),
		/no longer the directory this suite created/);
	assert.equal(readFileSync(join(root, "theirs.txt"), "utf8"), "THEIRS");
	// The ownership record is KEPT when removal refuses, rather than being
	// silently discarded — but the hook then reports rather than deleting.
	assert.equal(ownsRoot(root), true);
	assert.throws(() => removeOwnedRoots(), /left 1 root\(s\) alone/);
	assert.equal(readFileSync(join(root, "theirs.txt"), "utf8"), "THEIRS");
	rmSync(root, { recursive: true, force: true });
	// Now that the impostor is gone the record drains normally.
	removeOwnedRoots();
	assert.equal(ownsRoot(root), false);
});

// A registered root's pathname, taken over by something that is not a
// directory. Both takeovers below share this shape, and the point of each
// is that "not a directory" is not "not there".
//
// The target is built with the RAW primitive, for the same reason the
// link-nonfollowing case below does it: a registered target would be
// removed as a root of its own, and its disappearance would then prove
// nothing about what happened at the taken-over pathname.
function takenOverRoot(replace) {
	const root = ownedTemp("v12poc-impostor-");
	writeFileSync(join(root, "ours.txt"), "OURS");
	// Removed WITHOUT the registry, which is how this arises: the root goes
	// away underneath us and something else lands on the name.
	rmSync(root, { recursive: true, force: true });
	replace(root);
	return root;
}

test("W2907: a symbolic link at a root's pathname is not absence", () => {
	// Re-review 2026-08-22 [P1]. `identityOf()` answered `null` for an
	// absent path, a non-directory entry and an `lstat` failure alike, and
	// removal read every `null` as "already gone". So a symbolic link left
	// at a registered root's name made `removeOwnedRoot` report success and
	// DROP the ownership record while the link stood — cleanup claiming to
	// have removed a root it had actually walked away from.
	const target = mkdtempSync(join(tmpdir(), "w2907-takeover-target-"));
	try {
		writeFileSync(join(target, "precious.txt"), "PRECIOUS");
		mkdirSync(join(target, "subdir"), { recursive: true });
		writeFileSync(join(target, "subdir", "deep.txt"), "DEEP");

		const root = takenOverRoot((path) => symlinkSync(target, path));
		assert.throws(() => removeOwnedRoot(root),
			/is now a symbolic link, not the directory this suite created/);
		// Left alone means all three: the record kept, the link standing,
		// and the directory it points at untouched through it.
		assert.equal(ownsRoot(root), true, "a takeover silently disarmed cleanup");
		assert.equal(existsSync(root), true);
		assert.equal(readFileSync(join(target, "precious.txt"), "utf8"), "PRECIOUS");
		assert.equal(readFileSync(join(target, "subdir", "deep.txt"), "utf8"), "DEEP");
		// Retiring it is refused for the same reason: it is not absent, so
		// forgetting it would be forgetting a root that is still there.
		assert.throws(() => retireOwnedRoot(root, { observedAbsent: true }),
			/still exists; it cannot be retired as removed \(a symbolic link\)/);
		// And the suite hook reports rather than removing.
		assert.throws(() => removeOwnedRoots(), /left 1 root\(s\) alone/);
		assert.equal(existsSync(root), true);
		assert.equal(readFileSync(join(target, "precious.txt"), "utf8"), "PRECIOUS");

		unlinkSync(root);
		removeOwnedRoots();
		assert.equal(ownsRoot(root), false);
	} finally {
		rmSync(target, { recursive: true, force: true });
	}
});

test("W2907: a regular file at a root's pathname is not absence either", () => {
	// The same defect, without a link to follow: the entry itself is the
	// thing that would have been silently abandoned.
	const root = takenOverRoot((path) => writeFileSync(path, "NOT OURS"));
	assert.throws(() => removeOwnedRoot(root),
		/is now a regular file, not the directory this suite created/);
	assert.equal(ownsRoot(root), true);
	assert.equal(readFileSync(root, "utf8"), "NOT OURS");
	assert.throws(() => retireOwnedRoot(root, { observedAbsent: true }),
		/still exists; it cannot be retired as removed \(a regular file\)/);
	assert.throws(() => removeOwnedRoots(), /left 1 root\(s\) alone/);
	assert.equal(readFileSync(root, "utf8"), "NOT OURS",
		"suite cleanup removed a replacement entry");

	unlinkSync(root);
	removeOwnedRoots();
	assert.equal(ownsRoot(root), false);
});

test("W2907: removal unlinks a symbolic link instead of following it", () => {
	// The property `removeOwnedRoots` depends on, proven directly rather
	// than trusted. `placement.test.mjs` spends four cases establishing
	// that path shape is not ownership evidence; cleanup that resolved a
	// link would walk straight past all of it.
	//
	// The target is built with the RAW primitive and disposed by this
	// test, because it has to be a root the registry does not know: a
	// registered one would be removed as a root, and its disappearance
	// would then prove nothing about following the link that pointed at
	// it. This is the one place in the suite that reaches past the
	// registry, and it is the test OF the registry.
	const target = mkdtempSync(join(tmpdir(), "w2907-unregistered-"));
	try {
		writeFileSync(join(target, "keep.txt"), "KEEP");
		mkdirSync(join(target, "subdir"), { recursive: true });
		writeFileSync(join(target, "subdir", "deep.txt"), "DEEP");

		const linker = ownedTemp("v12poc-impostor-");
		symlinkSync(target, join(linker, "link-to-dir"));
		symlinkSync(join(target, "keep.txt"), join(linker, "link-to-file"));
		symlinkSync("/nonexistent-w2907", join(linker, "dangling"));

		assert.ok(removeOwnedRoots().includes(linker));
		assert.equal(existsSync(linker), false, "the owned root survived");
		assert.equal(readFileSync(join(target, "keep.txt"), "utf8"), "KEEP",
			"cleanup followed a symbolic link out of the root it was removing");
		assert.equal(readFileSync(join(target, "subdir", "deep.txt"), "utf8"), "DEEP");
	} finally {
		rmSync(target, { recursive: true, force: true });
	}
});

test("W2907: the registry only ever removes what it handed out", () => {
	// There is no way to register a path from outside. That is what makes
	// "this suite created it" a fact rather than an inference from the
	// name — the distinction the whole placement module exists to enforce.
	const before = ownedRoots();
	const root = ownedTemp("v12poc-test-");
	assert.deepEqual(ownedRoots(), [...before, root]);
	// A prefix is ONE path component: without that, a separator would
	// build a root outside the temporary directory and then hand it to a
	// recursive removal.
	for (const bad of ["../escape", "a/b", "/absolute", "", "..", "-leading"]) {
		assert.throws(() => ownedTemp(bad), /must be one path component/, bad);
	}
	assert.throws(() => ownedTemp(undefined), /must be one path component/);
	// Cleanup is idempotent and FORGETS, so a second call is a no-op
	// rather than a second attempt on a path something else may since
	// have created at that name.
	assert.ok(removeOwnedRoots().includes(root));
	assert.deepEqual(removeOwnedRoots(), []);
	assert.deepEqual(ownedRoots(), []);
});
