// A DELIBERATELY FAILING test file, driven by `fixture_cleanup.test.mjs`.
//
// `baton:work/records/2026/08/finding-v12-test-fixture-audit-follow-up/`.
// The defect W30 found is a failure-path defect: cleanup that runs on the
// successful tail of a test leaks every root the moment an assertion
// throws. Proving the correction therefore needs a test run that FAILS,
// and a failing test cannot live in the suite it is proving.
//
// So this file is named `.mjs` rather than `.test.mjs`: `npm test` globs
// `test/*.test.mjs` and never reaches it. It runs only when the
// regression spawns it explicitly, with:
//
//   W2907_MODE   `pass` or `fail`
//   W2907_TARGET an EXTERNAL directory this file links to and must not
//                touch — the parent asserts afterwards that it survived
//   TMPDIR       a parent the regression owns, so every root created here
//                is inside a blast radius the regression can inventory

import { test, after } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, readFileSync, symlinkSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import { ownedRoots, ownedTemp, removeOwnedRoots } from "../owned_roots.mjs";

const mode = process.env.W2907_MODE ?? "pass";
const target = process.env.W2907_TARGET;
const report = process.env.W2907_REPORT;
assert.ok(target, "the probe needs an external symlink target");
assert.ok(report, "the probe needs a parent-nominated report file");

// The report goes to a FILE the PARENT nominated, synchronously.
//
// Review 2026-08-22 [P1]: it used to be printed on stdout and scraped from
// the child test runner's output. That channel depends on the runner's
// reporter and isolation settings — under the default isolation the
// reviewer's runtime hid the probe file's own stdout entirely, so both
// parent cases failed on a supported Node with "the probe reported no
// roots". A file the parent named is either there or it is not, and "not
// there" is then a diagnosable outcome rather than an empty parse.
//
// (This is the same correction W2928's race harness needed, for the same
// reason. I had already learned it there and did not carry it across.)
const state = { mode, tests: [], roots: [], reachedIntendedFailure: false };
const publish = () => {
	state.roots = ownedRoots();
	writeFileSync(report, JSON.stringify(state));
};

after(() => {
	// The roots are published BEFORE cleanup, so the parent asserts absence
	// against exact paths rather than against a scan.
	publish();
	removeOwnedRoots();
});

test("the probe creates fixture roots the way the suite does", () => {
	state.tests.push("creates");
	// One root per family shape the suite actually uses: a plain scratch
	// root, one with content, and one carrying links OUT of the tree.
	const plain = ownedTemp("v12poc-test-");
	const nested = ownedTemp("v12poc-placement-");
	mkdirSync(join(nested, "deep", "deeper"), { recursive: true });
	writeFileSync(join(nested, "deep", "deeper", "file.txt"), "fixture content");

	const linking = ownedTemp("v12poc-owned-");
	// The whole point of the non-following requirement: a link out of an
	// owned root to something the suite does NOT own. The real fixtures
	// build these deliberately — to other fixture roots, to the checkout,
	// and to production-shaped Baton homes — so cleanup that resolved one
	// would delete real data on the way past.
	symlinkSync(target, join(linking, "link-to-external-dir"));
	symlinkSync(join(target, "precious.txt"), join(linking, "link-to-external-file"));
	symlinkSync(plain, join(linking, "link-to-sibling-root"));
	symlinkSync("/nonexistent-w2907", join(linking, "dangling"));
	publish();
	assert.equal(ownedRoots().length, 3);
});

test("the probe fails on purpose when asked to", () => {
	state.tests.push("intended-failure");
	if (mode !== "fail") { publish(); return; }
	// Recorded BEFORE the assertion, so the parent can tell "reached the
	// intended failure and died there" from "died somewhere else". Proving
	// that from the runner's output alone is what the hidden-stdout defect
	// made impossible.
	state.reachedIntendedFailure = true;
	publish();
	assert.equal("W2907-INTENDED-FAILURE", "not-equal", "W2907-INTENDED-FAILURE");
});

test("more roots are created AFTER the failing test", () => {
	state.tests.push("after-failure");
	// A root made after the failure still has to be cleaned: `after` runs
	// once the file's tests are done, whatever they did.
	ownedTemp("v12poc-cli-stranger-");
	publish();
});
