// Content addressing for typed directory inputs and declared outputs.
// A manifest is the sorted list of (relative path, size, sha256) plus a
// single digest over that list, so "the input the worker saw" and "the
// output the manager accepted" are both checkable facts rather than
// claims. Traversal is explicit and refuses anything that is not a
// regular file or directory: a symlink inside a frozen result would
// make the digest describe something other than what a reader gets.

import { createHash } from "node:crypto";
import { readdirSync, readFileSync, lstatSync } from "node:fs";
import { join, relative, sep } from "node:path";

class ManifestError extends Error {}

export function sha256(buffer) {
	return createHash("sha256").update(buffer).digest("hex");
}

export function manifestOf(root, { maxEntries = 1000, maxBytes = 16 * 1024 * 1024 } = {}) {
	const entries = [];
	let total = 0;
	const walk = (dir) => {
		for (const name of readdirSync(dir).sort()) {
			const full = join(dir, name);
			const stat = lstatSync(full);
			if (stat.isSymbolicLink()) {
				throw new ManifestError(
					`${relative(root, full)} is a symbolic link; a manifest must `
					+ `describe exactly what a reader gets, so links are refused`);
			}
			if (stat.isDirectory()) { walk(full); continue; }
			if (!stat.isFile()) {
				throw new ManifestError(
					`${relative(root, full)} is neither a regular file nor a directory`);
			}
			if (entries.length >= maxEntries) {
				throw new ManifestError(`more than ${maxEntries} entries under ${root}`);
			}
			total += stat.size;
			if (total > maxBytes) {
				throw new ManifestError(`more than ${maxBytes} bytes under ${root}`);
			}
			entries.push({
				path: relative(root, full).split(sep).join("/"),
				bytes: stat.size,
				sha256: sha256(readFileSync(full)),
			});
		}
	};
	walk(root);
	entries.sort((a, b) => (a.path < b.path ? -1 : a.path > b.path ? 1 : 0));
	const canonical = entries.map((e) => `${e.sha256}  ${e.bytes}  ${e.path}`).join("\n");
	return { entries, digest: sha256(Buffer.from(`${canonical}\n`, "utf8")) };
}

// Containment is checked on the manifest, not on the filesystem, so the
// answer is about the frozen bytes rather than a racing directory.
export function assertContained(manifest, allowed) {
	const permitted = new Set(allowed);
	for (const entry of manifest.entries) {
		if (!permitted.has(entry.path)) {
			throw new ManifestError(
				`the result contains ${JSON.stringify(entry.path)}, which the Job `
				+ `did not declare; declared: ${[...permitted].join(", ") || "(none)"}`);
		}
	}
	return manifest;
}

export { ManifestError };
