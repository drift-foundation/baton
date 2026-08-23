// The test-owned fixture-root registry.
//
// `baton:work/records/2026/08/finding-v12-test-fixture-audit-follow-up/`,
// the explicit follow-up to the cancelled W30. One isolated run of this
// suite left 162 `v12poc-test-*` roots behind, plus a
// `v12poc-absent-parent-*` and a `v12poc-cli-stranger-*` root from a
// FAILED assertion, because the cleanup that existed ran only on the
// successful tail of each test.
//
// WHY A REGISTRY AND NOT A SWEEP. The obvious fix — remove everything
// under the temporary directory matching `v12poc-*` — is the exact
// hazard `placement.mjs` exists to refuse, and `placement.test.mjs`
// spends four cases proving that path shape is not ownership evidence.
// A host path that matches a fixture prefix was not necessarily created
// by this suite: a concurrent run, another checkout, or anything at all
// may own it. So the only removable paths are the ones this module
// HANDED OUT, recorded at the instant it created them. There is no way
// to register a path from outside, which is what makes "we created it"
// a fact rather than an inference.
//
// WHY REMOVAL MUST NOT FOLLOW LINKS. These fixtures deliberately build
// symbolic links out of their roots — to other fixture roots, to this
// checkout, and to production-shaped Baton homes — because refusing to
// follow them is what several cases are testing. Cleanup that resolved
// one would delete somebody's real data on the way past.
// `fs.rmSync(recursive)` unlinks a symbolic link rather than descending
// through it, which is the property this module depends on; the
// regression in `fixture_cleanup.test.mjs` proves it rather than
// trusting it.
//
// WHY THE HOOK IS ADDITIVE. Existing in-test removals stay exactly where
// they are. Several cases remove a root mid-test, or retain one long
// enough to assert a refusal against it, and suite cleanup runs only
// after the module's tests have finished. Removal is idempotent, so a
// root already gone is not an error.

import { lstatSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

// Exact roots, in creation order, each recorded with the IDENTITY of the
// directory that was created — not just its pathname.
//
// Review 2026-08-22 [P1]: recording a path string alone made the registry
// claim ownership of a NAME. Six placement families are removed by their
// own test tails before the suite hook runs, and once a test deletes a
// root the suite owns nothing at that pathname. The reviewer created a
// root, deleted it the way those tails do, recreated the same pathname
// with a replacement marker, and the hook deleted the replacement — the
// exact path-identity ABA that `placement.mjs` spends four cases refusing.
//
// Two corrections, and the first is the one that matters:
//
//   1. Removal and forgetting are ONE action. `removeOwnedRoot` and
//      `retireOwnedRoot` are how a test drops a root early, so the
//      registry never holds a pathname it no longer owns.
//   2. `dev`/`ino` are recorded at creation and re-checked immediately
//      before removal. A pathname that now resolves to a different
//      directory is refused rather than removed. That narrows the window
//      rather than closing it — nothing between `lstat` and `rm` is
//      atomic — so it is a second line, not the first.
//   3. Re-review 2026-08-22 [P1]: that re-check answered with a bare
//      identity string or `null`, and `null` meant three incompatible
//      things at once. `inspect()` now separates absence, our directory,
//      somebody else's directory, a non-directory entry and an `lstat`
//      failure, because only the first of those is safely idempotent.
const owned = new Map();

// A fixture prefix is ONE path component. Without this, a prefix carrying
// a separator would build a root outside the temporary directory and then
// hand it to a recursive removal.
const PREFIX = /^[A-Za-z0-9][A-Za-z0-9._-]*$/;

// What is at this pathname RIGHT NOW, as four states that mean four
// different things.
//
// Re-review 2026-08-22 [P1]: this returned one `null` for all of "nothing
// is there", "something that is not a directory is there" and "the
// question could not be answered". Removal read that `null` as idempotent
// absence, so replacing a registered root with a symbolic link made
// cleanup report success, forget the root, and leave the replacement
// entry standing. Absence is the ONLY state that is safe to treat as
// already-done; everything else keeps the ownership record and reports.
//
// `lstat` is deliberate: it never follows the final component, so a
// symbolic link at a root's pathname is seen as a link rather than as
// whatever it points at.
function inspect(path) {
	let stat;
	try {
		stat = lstatSync(path);
	} catch (error) {
		// Only ENOENT is absence. ENOTDIR, EACCES, EIO and the rest are
		// unanswered questions, and a recursive removal is not the thing to
		// do with one of those.
		if (error.code === "ENOENT") return { state: "absent" };
		return { state: "error", error };
	}
	if (stat.isDirectory()) return { state: "directory", identity: `${stat.dev}:${stat.ino}` };
	return { state: "other", kind: entryKind(stat) };
}

function entryKind(stat) {
	if (stat.isSymbolicLink()) return "symbolic link";
	if (stat.isFile()) return "regular file";
	if (stat.isFIFO()) return "FIFO";
	if (stat.isSocket()) return "socket";
	if (stat.isBlockDevice()) return "block device";
	if (stat.isCharacterDevice()) return "character device";
	return "non-directory entry";
}

// The only way to create a fixture root. It registers at the instant it
// creates, so there is no window in which a root exists unrecorded and no
// path can be registered that this module did not make.
export function ownedTemp(prefix) {
	if (typeof prefix !== "string" || !PREFIX.test(prefix)) {
		throw new Error(
			`fixture prefix ${JSON.stringify(prefix)} must be one path component `
			+ `of letters, digits, '.', '_' and '-'`);
	}
	const parent = tmpdir();
	const root = mkdtempSync(join(parent, prefix));
	// Belt and braces: what `mkdtemp` returned really is a direct child of
	// the temporary directory. The registry's whole promise is that it only
	// ever removes roots of that shape.
	if (resolve(root, "..") !== resolve(parent)) {
		rmSync(root, { recursive: true, force: true });
		throw new Error(`fixture root ${root} is not a direct child of ${parent}`);
	}
	// A root enters the registry with a REAL directory identity or it does
	// not enter it at all. Recording an unknown identity would put an entry
	// in the map that later removal has no way to check.
	const made = inspect(root);
	if (made.state !== "directory") {
		rmSync(root, { recursive: true, force: true });
		throw new Error(`fixture root ${root} is not a directory at creation `
			+ `(${describe(made)}); it was not registered`);
	}
	owned.set(root, made.identity);
	return root;
}

// A copy, for a caller that needs to report or assert on what it made.
export function ownedRoots() { return [...owned.keys()]; }

export function ownsRoot(path) { return owned.has(path); }

// Remove ONE root and forget it, as one action.
//
// This is what a test tail calls instead of `rmSync`. Doing the two
// separately is what left a dead pathname armed for the suite hook.
export function removeOwnedRoot(path) {
	if (!owned.has(path)) {
		throw new Error(
			`${path} is not a registered fixture root; this registry removes only `
			+ `what it handed out`);
	}
	removeExactly(path, owned.get(path));
	owned.delete(path);
	return path;
}

// Forget a root WITHOUT removing it, for one the product path under test
// has already deleted. The caller passes the positively observed absence;
// retiring a root that is still there would strand it.
export function retireOwnedRoot(path, { observedAbsent }) {
	if (!owned.has(path)) {
		throw new Error(`${path} is not a registered fixture root`);
	}
	if (observedAbsent !== true) {
		throw new Error(
			`retiring ${path} needs the positively observed absence that justifies `
			+ `it; a root that is still there would be stranded`);
	}
	const now = inspect(path);
	if (now.state === "error") {
		throw new Error(`${path} could not be confirmed absent (${describe(now)}); `
			+ `it stays registered`);
	}
	if (now.state !== "absent") {
		throw new Error(`${path} still exists; it cannot be retired as removed `
			+ `(${describe(now)})`);
	}
	owned.delete(path);
	return path;
}

// The one place a state is turned into words, so the four of them read the
// same wherever they are reported.
function describe(state) {
	if (state.state === "absent") return "absent";
	if (state.state === "directory") return `directory ${state.identity}`;
	if (state.state === "other") return `a ${state.kind}`;
	return `lstat failed with ${state.error.code ?? state.error.message}`;
}

// Remove exactly the directory this registry created at `path`.
//
// If the pathname is anything other than that exact directory it is NOT
// ours, whatever it is called, and removing it is the mistake this module
// exists to avoid. Absence is the only state that returns quietly: it is
// what makes cleanup idempotent, and it is the only one where there is
// nothing left to get wrong.
function removeExactly(path, expected) {
	const now = inspect(path);
	if (now.state === "absent") return;
	if (now.state === "error") {
		throw new Error(
			`${path} could not be inspected (${describe(now)}); a root this suite `
			+ `cannot identify is left alone`);
	}
	if (now.state === "other") {
		throw new Error(
			`${path} is now ${describe(now)}, not the directory this suite created; `
			+ `a matching pathname is not ownership evidence, so it is left alone`);
	}
	if (now.identity !== expected) {
		throw new Error(
			`${path} is no longer the directory this suite created `
			+ `(${expected} -> ${now.identity}); a matching pathname is not `
			+ `ownership evidence, so it is left alone`);
	}
	rmSync(path, { recursive: true, force: true });
}

// Remove exactly the recorded roots and nothing else.
//
// A root is forgotten only AFTER its removal succeeds: popping first would
// silently discard the ownership record of a root that is still there.
// Removal is link-nonfollowing by `rmSync`'s recursive semantics.
export function removeOwnedRoots() {
	const removed = [];
	const failures = [];
	for (const path of [...owned.keys()].reverse()) {
		try {
			removeExactly(path, owned.get(path));
		} catch (error) {
			failures.push(error.message);
			continue;
		}
		owned.delete(path);
		removed.push(path);
	}
	if (failures.length) {
		throw new Error(`suite cleanup left ${failures.length} root(s) alone:\n`
			+ failures.map((line) => `  ${line}`).join("\n"));
	}
	return removed;
}
