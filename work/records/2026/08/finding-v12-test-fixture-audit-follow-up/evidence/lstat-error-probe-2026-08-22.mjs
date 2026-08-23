// Out-of-suite probe for the fourth inspect() state: an lstat that FAILS
// for a reason other than absence. It is not a suite regression because
// inducing it needs a chmod on the temporary directory itself, which no
// other test in the file could tolerate.
import { chmodSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import assert from "node:assert/strict";

if (process.getuid() === 0) { console.log("SKIP: root defeats the permission"); process.exit(2); }
const parent = mkdtempSync(join(tmpdir(), "w2907-lstat-error-"));
process.env.TMPDIR = parent;
const { ownedTemp, ownsRoot, removeOwnedRoot, removeOwnedRoots, retireOwnedRoot }
	= await import("/home/sl/src/baton/v12/test/owned_roots.mjs");
try {
	const root = ownedTemp("v12poc-test-");
	chmodSync(parent, 0o600);            // drop search permission
	assert.throws(() => removeOwnedRoot(root), /could not be inspected \(lstat failed with EACCES\)/);
	assert.equal(ownsRoot(root), true, "an unanswerable lstat dropped the ownership record");
	assert.throws(() => retireOwnedRoot(root, { observedAbsent: true }),
		/could not be confirmed absent \(lstat failed with EACCES\)/);
	assert.throws(() => removeOwnedRoots(), /left 1 root\(s\) alone/);
	assert.equal(ownsRoot(root), true);
	chmodSync(parent, 0o700);
	assert.deepEqual(removeOwnedRoots(), [root]);
	assert.equal(ownsRoot(root), false);
	console.log("PASS: an lstat failure fails closed and keeps the record");
} finally {
	chmodSync(parent, 0o700);
	rmSync(parent, { recursive: true, force: true });
}
