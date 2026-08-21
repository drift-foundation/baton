// THE placement authority: one fail-closed, non-destructive validation
// that every state-creating and state-deleting entry point runs before
// its first mutation.
//
// `finding-v12-in-repository-migration`, review round 1. The prototype
// moved into the Baton checkout as `v12/`, and the first migration
// pass moved its disposable state out to an explicit external root —
// but each entry point still reached its `rm -rf` from RAW configured
// strings. `run-proof.sh` removed an evidence directory built from an
// unconstrained label before anything validated the configuration;
// `new-authority.sh` removed whatever authority operand it was handed;
// `state-clean` removed a raw `state_root` guarded only by a short
// denylist. The exported check accepted `/tmp` as a state root, and
// compared externality against `v12/` alone — so a sibling INSIDE the
// checkout passed. None of that is an invalid-configuration branch
// nobody reaches: a typo in a label or a root is enough.
//
// So the rule is: nothing is created or deleted until this module has
// approved it, and this module never creates or deletes anything.
//
// It is not the security boundary either. `assertNoBatonCapability`
// remains the canonicalized launch-time fence that decides what a
// container may mount, and nothing here replaces it. This decides
// where the prototype's own setup and cleanup are allowed to write.

import { existsSync, readFileSync, realpathSync } from "node:fs";
import { basename, dirname, isAbsolute, join, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

class PlacementError extends Error {}

// Both roots come from this module's own location. Nothing infers them
// from a configured value, an environment variable or a cwd.
export const POC_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const CHECKOUT_ROOT = resolve(POC_ROOT, "..");

// A COURTESY refusal, not the authorization. These are the roots a typo
// most easily produces, and naming them gives a clearer message than
// "unowned". What actually authorizes deletion is
// `assertOwnedStateRoot` below — round-2 review was right that no finite
// denylist and no depth threshold can prove a directory belongs to this
// prototype, because `/var/log`, `/usr/local` and `~/Documents` all pass
// both and none of them is ours.
const BROAD_ROOTS = new Set([
	"/", "/bin", "/boot", "/dev", "/etc", "/home", "/lib", "/lib64", "/media",
	"/mnt", "/opt", "/proc", "/root", "/run", "/sbin", "/srv", "/sys", "/tmp",
	"/usr", "/var", "/var/tmp",
]);
// `/tmp/baton-v12-poc` is two. One component is always a top-level
// directory, whatever it is called. Also a courtesy refusal.
const MIN_DEPTH = 2;

// POSITIVE, DURABLE OWNERSHIP EVIDENCE (round-2 review). A state root
// that already exists is only deletable when it carries this marker
// naming ITSELF, so a marker copied from elsewhere authorizes nothing.
// A root that does not exist yet is fresh: creating it is how ownership
// is established, deliberately, by the one recipe that creates it.
export const OWNER = "baton-v12-poc";
export const MARKER_NAME = ".v12-poc-state-root";

export function markerPath(root) { return join(root, MARKER_NAME); }

export function markerContent(root) {
	return `${JSON.stringify({
		owner: OWNER,
		root,
		checkout: CHECKOUT_ROOT,
		"//": "This directory is the disposable state root of the Baton v12 "
			+ "proof of concept. `just state-clean` recursively REMOVES it, and "
			+ "refuses to remove any existing directory that does not carry this "
			+ "marker naming itself. Delete this file and the prototype will "
			+ "refuse to clean the directory rather than guess.",
	}, null, 2)}\n`;
}

// `fresh` — the root does not exist; whoever creates it owns it.
// `owned` — it exists and carries our marker naming this exact root.
// Anything else REFUSES, and refusing is the whole point: an existing
// directory that is not demonstrably ours never reaches `rm -rf`.
export function ownershipOf(root) {
	if (!existsSync(root)) return "fresh";
	const marker = markerPath(root);
	if (!existsSync(marker)) {
		fail(`state_root ${root} already exists and carries no ${MARKER_NAME}. `
			+ `This directory is recursively REMOVED by the prototype's cleanup, `
			+ `so it is only ever a directory this prototype created for itself. `
			+ `Point state_root at a path that does not exist yet, or at one that `
			+ `already carries the marker`);
	}
	let recorded;
	try { recorded = JSON.parse(readFileSync(marker, "utf8")); }
	catch (error) {
		fail(`the ownership marker at ${marker} is unreadable or not JSON `
			+ `(${error.message}); a marker that cannot be read is not evidence`);
	}
	if (recorded?.owner !== OWNER) {
		fail(`the ownership marker at ${marker} names owner `
			+ `${JSON.stringify(recorded?.owner)}, not ${OWNER}`);
	}
	// Naming ITSELF is what stops a marker copied into an unrelated
	// directory from authorizing that directory's deletion.
	if (resolve(String(recorded?.root ?? "")) !== root) {
		fail(`the ownership marker at ${marker} names root `
			+ `${JSON.stringify(recorded?.root)}, not ${root}; a marker copied `
			+ `from another root authorizes nothing`);
	}
	return "owned";
}

// The gate every DESTRUCTIVE use of the root passes. Setup uses
// `assertStateRoot` and may find the root `fresh`; cleanup requires
// `owned` and accepts nothing else.
//
// Round-3 review: this used to let an ABSENT root through on the
// deletion path, on the reasoning that there was nothing there to
// remove. That is not a property of the moment the check runs. The
// value it returned was fed straight to `chmod -R` and `rm -rf`, and
// anything could create an unrelated directory at that path in
// between — cleanup would then act on a directory that never carried
// a marker, which is exactly what the ownership rule exists to
// prevent. `owned` or nothing: the caller gets no path to remove.
export function assertOwnedStateRoot(value, { forDeletion = false } = {}) {
	const root = assertStateRoot(value);
	const state = ownershipOf(root);
	// `ownershipOf` already refused every EXISTING root that is not
	// ours, by name, so the only state that reaches here is `fresh` —
	// an absent root. The condition stays written as "not owned"
	// because that is the rule; it does not depend on that reasoning
	// holding after a later edit.
	if (forDeletion && state !== "owned") {
		fail(`state_root ${root} does not exist, so there is nothing this `
			+ `prototype owns to remove. Cleanup answers only for a root `
			+ `carrying ${MARKER_NAME}; returning an absent path would hand `
			+ `a recursive remove to whatever happens to be created there `
			+ `next`);
	}
	return { root, state };
}
// One path component, and nothing that could traverse out of the
// evidence directory or collide with a dotted entry.
const LABEL = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/;

function fail(message) { throw new PlacementError(`v12-poc placement: ${message}`); }

function within(root, path) { return path === root || path.startsWith(root + sep); }

function depth(path) { return path.split(sep).filter(Boolean).length; }

// Resolve as far as the filesystem actually goes, so a symlinked state
// root is judged by where it LANDS rather than by how it is spelled.
// A path that does not exist yet is judged lexically, which is all
// there is to judge — and it will exist under a parent that was itself
// checked here.
export function canonicalize(path) {
	let probe = resolve(path);
	const tail = [];
	while (!existsSync(probe)) {
		const parent = dirname(probe);
		if (parent === probe) return resolve(path);
		tail.unshift(basename(probe));
		probe = parent;
	}
	try { return join(realpathSync(probe), ...tail); }
	catch { return resolve(path); }
}

// Every path that reaches a shell entry point goes through here. The
// whitespace rule is not cosmetic: these values are read with `read -r`
// into positional shell variables, and a path with a space in it would
// silently split into two.
export function assertSafeAbsolute(what, value) {
	if (typeof value !== "string" || !value.trim()) {
		fail(`${what} must be a non-empty string`);
	}
	if (!isAbsolute(value)) fail(`${what} ${value} must be an absolute path`);
	if (/[\s\u0000-\u001f]/.test(value)) {
		fail(`${what} ${value} contains whitespace or a control character; these `
			+ `paths cross shell entry points and must be unambiguous`);
	}
	return resolve(value);
}

// The one root. Refused unless it is external to the WHOLE checkout —
// not merely outside `v12/`, which is what round 1 found — specific
// enough that removing it removes only this prototype's own state, and
// not an ancestor of the operator's home.
export function assertStateRoot(value) {
	const root = assertSafeAbsolute("state_root", value);
	const home = process.env.HOME && isAbsolute(process.env.HOME)
		? resolve(process.env.HOME) : null;
	// Both spellings: as written, and where it actually lands.
	for (const candidate of new Set([root, canonicalize(root)])) {
		if (BROAD_ROOTS.has(candidate) || depth(candidate) < MIN_DEPTH) {
			fail(`state_root ${candidate} is a filesystem-wide or top-level directory. `
				+ `This root is created, written into and recursively REMOVED by the `
				+ `prototype's own recipes, so it must be a directory that exists for `
				+ `nothing else`);
		}
		if (within(CHECKOUT_ROOT, candidate) || within(candidate, CHECKOUT_ROOT)) {
			fail(`state_root ${candidate} overlaps the Baton checkout at ${CHECKOUT_ROOT}. `
				+ `Every disposable path lives OUTSIDE the checkout: the runtime fence `
				+ `refuses to mount anything inside it into a worker, and setup and `
				+ `cleanup must not write or delete there either`);
		}
		if (home && within(candidate, home)) {
			fail(`state_root ${candidate} contains the home directory ${home}`);
		}
	}
	return root;
}

// A destructive or state-creating operand. STRICT descendant: the root
// itself is removed only by the one recipe that owns it, and never as
// a by-product of removing an attempt directory or an evidence pack.
export function assertUnderStateRoot(what, root, value) {
	const path = assertSafeAbsolute(what, value);
	for (const candidate of new Set([path, canonicalize(path)])) {
		if (candidate === root || !within(root, candidate)) {
			fail(`${what} ${candidate} is not a strict descendant of the disposable `
				+ `state root ${root}; this path is created and recursively removed, so `
				+ `it is refused rather than bounded by hope`);
		}
	}
	return path;
}

export function assertLabel(value) {
	if (typeof value !== "string" || !LABEL.test(value)) {
		fail(`evidence label ${JSON.stringify(value)} must be ONE path component `
			+ `matching ${LABEL} — a label with a separator or a parent component `
			+ `escapes the evidence directory that is about to be removed`);
	}
	return value;
}

// A record path is relative and stays inside its base, for the same
// reason: it is joined onto the record base and the result is written.
export function assertRecordPath(value) {
	if (typeof value !== "string" || !value.trim()) fail("record_path must be a non-empty string");
	if (isAbsolute(value) || /[\s\u0000-\u001f]/.test(value)) {
		fail(`record_path ${value} must be a relative path with no whitespace`);
	}
	if (value.split("/").some((part) => part === ".." || part === "")) {
		fail(`record_path ${value} must not traverse out of the record base`);
	}
	return value;
}

// The complete plan every entry point works from. Nothing outside this
// object is a legitimate target for creation or removal, and computing
// it cannot mutate anything.
export function planPlacement(raw, { label = null } = {}) {
	if (!raw || typeof raw !== "object") fail("the configuration must be a JSON object");
	const root = assertStateRoot(raw.state_root);
	const configPath = assertUnderStateRoot("baton.config", root, raw.baton?.config);
	const plan = {
		stateRoot: root,
		authority: assertUnderStateRoot("the authority directory", root, dirname(configPath)),
		batonConfig: configPath,
		recordBase: assertUnderStateRoot("record_base", root, raw.record_base),
		recordPath: assertRecordPath(raw.record_path),
		stateDir: assertUnderStateRoot("runtime.state_dir", root, raw.runtime?.state_dir),
	};
	if (label !== null) {
		plan.label = assertLabel(label);
		plan.evidence = assertUnderStateRoot("the evidence directory", root,
			join(root, "evidence", plan.label));
	}
	return plan;
}

export { PlacementError };

// -- The shell entry point ---------------------------------------------
//
// The scripts call this BEFORE their first `mkdir`, `chmod` or
// `rm -rf`, and use the values it prints rather than the raw strings
// they were configured with. One line, space-separated, which is safe
// precisely because every value was checked for whitespace above.
//
// Importing this module prints nothing: `config.mjs` imports it during
// ordinary validation.

export const USAGE =
	"usage: node src/placement.mjs plan   --config <poc.json> --label <label>\n"
	+ "       node src/placement.mjs paths  --config <poc.json>\n"
	+ "       node src/placement.mjs own    --config <poc.json>\n"
	+ "       node src/placement.mjs marker --config <poc.json>\n"
	+ "       node src/placement.mjs state  --config <poc.json>";

function operands(argv) {
	const out = {};
	for (let index = 0; index < argv.length; index += 1) {
		const flag = argv[index];
		const value = argv[index + 1];
		if (flag === "--config" || flag === "--label") {
			out[flag.slice(2)] = value;
			index += 1;
			continue;
		}
		fail(`unknown operand ${JSON.stringify(flag)}`);
	}
	return out;
}

export async function main(argv) {
	const [verb, ...rest] = argv;
	const options = operands(rest);
	const verbs = ["plan", "paths", "own", "marker", "state"];
	if (!verbs.includes(verb)) fail(`unknown verb ${JSON.stringify(verb)}`);
	if (!options.config) fail("--config <poc.json> is required");
	const raw = JSON.parse(readFileSync(resolve(options.config), "utf8"));

	// `state` feeds DELETION and nothing else, so it demands ownership.
	// Round-2 review: a mistyped existing directory used to reach
	// `chmod -R` and `rm -rf` on path shape alone.
	if (verb === "state") {
		const { root } = assertOwnedStateRoot(raw.state_root, { forDeletion: true });
		return `${root}\n`;
	}
	if (verb === "marker") return markerContent(assertStateRoot(raw.state_root));
	// `own` is what SETUP calls: it refuses an existing root that is not
	// ours, and otherwise prints where the marker belongs and whether the
	// caller is about to establish ownership or merely confirm it.
	if (verb === "own") {
		const { root, state } = assertOwnedStateRoot(raw.state_root);
		return `${markerPath(root)} ${state}\n`;
	}
	const plan = planPlacement(raw,
		verb === "plan" ? { label: options.label ?? fail("plan needs --label <label>") }
		                : {});
	const fields = [plan.stateRoot, plan.authority, plan.recordBase,
	                plan.recordPath, plan.stateDir];
	if (verb === "plan") fields.push(plan.evidence);
	return `${fields.join(" ")}\n`;
}

function invokedDirectly(entry) {
	if (!entry) return false;
	try { return realpathSync(entry) === realpathSync(fileURLToPath(import.meta.url)); }
	catch { return false; }
}

if (invokedDirectly(process.argv[1])) {
	try {
		process.stdout.write(await main(process.argv.slice(2)));
	} catch (error) {
		if (!(error instanceof PlacementError)) throw error;
		process.stderr.write(`${error.message}\n${USAGE}\n`);
		process.exit(2);
	}
}
