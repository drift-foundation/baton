// Typed-input source validation.
//
// A Job's `job.in.json` is an UNTRUSTED descriptor: it arrives through
// the bound record and names where the input lives. Resolving it without
// a boundary check, and then copying with symlink dereference, turns
// that descriptor into arbitrary host-file disclosure — a record-local
// `input` symlink pointing at any directory on the host materializes as
// ordinary files in the worker snapshot, and every downstream digest
// then faithfully describes content the Job was never entitled to.
//
// So containment is established BEFORE anything is copied, on the real
// path as well as the lexical one, and the copy never follows a link.

import { copyFileSync, lstatSync, mkdirSync, readdirSync, realpathSync }
	from "node:fs";
import { isAbsolute, join, normalize, relative, resolve, sep } from "node:path";

class InputSourceError extends Error {}

function within(child, parent) {
	if (child === parent) return true;
	const rel = relative(parent, child);
	return rel !== "" && !rel.startsWith("..") && !isAbsolute(rel);
}

// `declared` is the relative path exactly as the Job document spelled it.
// Both the spelling and the resolved reality are checked: the first
// rejects the obvious `../../etc`, the second rejects the symlink that
// looks perfectly ordinary until it is followed.
export function resolveInputSource(recordDir, declared) {
	if (typeof declared !== "string" || !declared.trim()) {
		throw new InputSourceError("the Job declares no input source path");
	}
	if (isAbsolute(declared)) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} is absolute; a Job's typed input `
			+ `must live inside its own bound record`);
	}
	if (normalize(declared).split(sep).includes("..")) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} traverses outside its bound record`);
	}
	const source = resolve(recordDir, declared);
	if (!within(source, resolve(recordDir))) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} resolves outside its bound record`);
	}
	// A symlink AT the root is the case that survives a lexical check and
	// still escapes, so it is named separately rather than folded in.
	let stat;
	try { stat = lstatSync(source); }
	catch (error) {
		throw new InputSourceError(`input source ${JSON.stringify(declared)}: ${error.message}`);
	}
	if (stat.isSymbolicLink()) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} is a symbolic link; the manager will `
			+ `not follow a link out of the bound record`);
	}
	if (!stat.isDirectory()) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} is not a directory`);
	}
	let real;
	let realBase;
	try {
		real = realpathSync(source);
		realBase = realpathSync(recordDir);
	} catch (error) {
		throw new InputSourceError(`input source ${JSON.stringify(declared)}: ${error.message}`);
	}
	if (!within(real, realBase)) {
		throw new InputSourceError(
			`input source ${JSON.stringify(declared)} really lives at ${real}, outside the `
			+ `bound record at ${realBase}`);
	}
	return source;
}

// A copy that cannot import anything the source tree did not literally
// contain: every entry is lstat-ed, and anything that is not a directory
// or a regular file — a symlink, a socket, a device — is refused rather
// than skipped. Refusing is the point; skipping would silently produce a
// snapshot that does not match the Job's input.
export function copyTreeStrict(source, dest, { maxEntries = 1000,
                                               maxBytes = 16 * 1024 * 1024 } = {}) {
	let entries = 0;
	let bytes = 0;
	const walk = (from, to) => {
		mkdirSync(to, { recursive: true });
		for (const name of readdirSync(from).sort()) {
			const child = join(from, name);
			const target = join(to, name);
			const stat = lstatSync(child);
			if (stat.isSymbolicLink()) {
				throw new InputSourceError(
					`${relative(source, child)} is a symbolic link; the manager copies only `
					+ `what the input directory literally contains`);
			}
			if (stat.isDirectory()) { walk(child, target); continue; }
			if (!stat.isFile()) {
				throw new InputSourceError(
					`${relative(source, child)} is neither a regular file nor a directory`);
			}
			entries += 1;
			bytes += stat.size;
			if (entries > maxEntries) {
				throw new InputSourceError(`the input has more than ${maxEntries} entries`);
			}
			if (bytes > maxBytes) {
				throw new InputSourceError(`the input is larger than ${maxBytes} bytes`);
			}
			copyFileSync(child, target);
		}
	};
	walk(source, dest);
	return { entries, bytes };
}

export { InputSourceError };
