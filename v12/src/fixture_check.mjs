// The independent expected-result computation. The manager NEVER asks
// the agent whether its own answer was right: it recomputes the
// transformation here from the same read-only input and compares.
//
// The rule is stated once, in `INDEX_RULE`, and that exact text is what
// the Job contract hands the agent — so the agent and the checker are
// working from one specification rather than two that might drift.

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

export const INDEX_VERSION = "0-spike";

export const INDEX_RULE = `Consider every regular file DIRECTLY inside the input directory whose name ends in ".md" or ".txt". Ignore everything else, and do not descend into subdirectories. Sort those filenames in ascending byte order. For each one produce an object with exactly these three fields:
  "path"    - the filename alone, with no directory part.
  "heading" - the first line of the file whose first non-whitespace character is "#", with all leading "#" characters and all surrounding whitespace removed. If the file has no such line, use null.
  "lines"   - the number of newline characters in the file, as an integer.
The result is a single JSON object with exactly two fields: "index_version", whose value is the string "${INDEX_VERSION}", and "entries", whose value is the array of those objects in the sorted order.`;

export function headingOf(text) {
	for (const line of text.split("\n")) {
		const trimmed = line.trim();
		if (trimmed.startsWith("#")) return trimmed.replace(/^#+/, "").trim();
	}
	return null;
}

export function expectedIndex(inputDir) {
	const names = readdirSync(inputDir)
		.filter((name) => name.endsWith(".md") || name.endsWith(".txt"))
		.filter((name) => statSync(join(inputDir, name)).isFile())
		.sort();
	return {
		index_version: INDEX_VERSION,
		entries: names.map((name) => {
			const text = readFileSync(join(inputDir, name), "utf8");
			return {
				path: name,
				heading: headingOf(text),
				lines: (text.match(/\n/g) ?? []).length,
			};
		}),
	};
}

// Structural equality on the PARSED value, deliberately not on bytes.
// Byte-identical model output is not something this proof needs, and
// requiring it would turn a formatting difference into a lifecycle
// failure. The bytes are still digest-bound; this checks meaning.
export function diffIndex(actual, expected) {
	const problems = [];
	// The rule says the result is an object with EXACTLY two fields. An
	// undeclared top-level field was previously accepted while an
	// undeclared field inside an entry was rejected — the same exactness
	// argument, applied at one level and not the other.
	for (const field of Object.keys(actual ?? {})) {
		if (!["index_version", "entries"].includes(field)) {
			problems.push(`the result has undeclared top-level field ${JSON.stringify(field)}`);
		}
	}
	if (actual?.index_version !== expected.index_version) {
		problems.push(`index_version is ${JSON.stringify(actual?.index_version)}, `
			+ `expected ${JSON.stringify(expected.index_version)}`);
	}
	if (!Array.isArray(actual?.entries)) {
		problems.push("entries is not an array");
		return problems;
	}
	if (actual.entries.length !== expected.entries.length) {
		problems.push(`entries has ${actual.entries.length} items, `
			+ `expected ${expected.entries.length}`);
	}
	const limit = Math.min(actual.entries.length, expected.entries.length);
	for (let index = 0; index < limit; index += 1) {
		const got = actual.entries[index];
		const want = expected.entries[index];
		for (const field of ["path", "heading", "lines"]) {
			if (JSON.stringify(got?.[field]) !== JSON.stringify(want[field])) {
				problems.push(`entries[${index}].${field} is ${JSON.stringify(got?.[field])}, `
					+ `expected ${JSON.stringify(want[field])}`);
			}
		}
		for (const field of Object.keys(got ?? {})) {
			if (!["path", "heading", "lines"].includes(field)) {
				problems.push(`entries[${index}] has undeclared field ${JSON.stringify(field)}`);
			}
		}
	}
	return problems;
}
