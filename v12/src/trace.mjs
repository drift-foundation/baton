// The machine-readable chronological trace. One JSONL file per attempt,
// append-only, written as it happens rather than reconstructed at the
// end — a trace assembled after the fact cannot prove ordering, and
// ordering is most of what this proof is about.
//
// Wall-clock timestamps are recorded for readability; the monotonic
// `seq` is what establishes order.

import { appendFileSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

const SECRET_KEYS = /(token|credential|secret|password|authorization)/i;

// Names that CONTAIN a secret-looking word but carry no secret. Without
// this the negative-proof evidence redacts its own subject: a trace that
// hides which token fault was injected cannot prove the fence held.
const SAFE_KEYS = new Set([
	"token_fault", "carried_token", "token_jti", "jti", "expires_at",
	"issued_at", "ttl_ms", "credential", "remaining_seconds",
]);

// Values that are secret-SHAPED regardless of what they are called. Key
// matching alone is not enough: this prototype's own claim token lives
// under the key "value", which no name-based rule would catch.
const SECRET_SHAPES = [
	/^[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{16,}$/,   // this prototype's claim handle
	/^sk-ant-[A-Za-z0-9_-]{8,}/,                   // Anthropic API key
	/^eyJ[A-Za-z0-9_-]{16,}\./,                    // a JWT
];

// Evidence must never carry credentials. Redaction happens at the trace
// boundary rather than at every call site, because one forgotten call
// site is a leaked token.
export function redact(value, depth = 0) {
	if (depth > 8) return "[deep]";
	if (Array.isArray(value)) return value.map((entry) => redact(entry, depth + 1));
	if (value && typeof value === "object") {
		const out = {};
		for (const [key, entry] of Object.entries(value)) {
			if (SECRET_KEYS.test(key) && !SAFE_KEYS.has(key)) {
				out[key] = typeof entry === "string"
					? `[redacted ${entry.length} chars]` : "[redacted]";
			} else out[key] = redact(entry, depth + 1);
		}
		return out;
	}
	if (typeof value === "string" && SECRET_SHAPES.some((shape) => shape.test(value))) {
		return `[redacted ${value.length} chars]`;
	}
	return value;
}

export class Trace {
	constructor(path, { now = () => new Date().toISOString() } = {}) {
		this.path = path;
		this.now = now;
		this.seq = 0;
		this.secrets = [];
		mkdirSync(dirname(path), { recursive: true });
	}

	// Shape and name matching are not enough. A streamed agent reply
	// arrives as many short chunks, and each individual chunk of a token
	// is far too short and far too ordinary-looking for either rule to
	// catch — while the concatenation of them is the whole credential.
	// Known secrets are therefore scrubbed by FRAGMENT: any run of 12 or
	// more characters that occurs inside a registered secret is removed.
	addSecret(value) {
		if (typeof value === "string" && value.length >= 24) this.secrets.push(value);
	}

	scrub(text) {
		let current = text;
		for (const secret of this.secrets) {
			let out = "";
			let index = 0;
			while (index < current.length) {
				let length = 0;
				while (index + length < current.length
						&& secret.includes(current.slice(index, index + length + 1))) {
					length += 1;
				}
				if (length >= 12) { out += `[redacted ${length} chars]`; index += length; }
				else { out += current[index]; index += 1; }
			}
			current = out;
		}
		return current;
	}

	scrubDeep(value, depth = 0) {
		if (depth > 8) return value;
		if (typeof value === "string") return this.scrub(value);
		if (Array.isArray(value)) return value.map((entry) => this.scrubDeep(entry, depth + 1));
		if (value && typeof value === "object") {
			return Object.fromEntries(Object.entries(value).map(
				([key, entry]) => [key, this.scrubDeep(entry, depth + 1)]));
		}
		return value;
	}

	// `detail` is NESTED rather than spread. A spread lets a recorded
	// payload carry its own `seq` — Baton results routinely do — and
	// silently overwrite the trace's ordering field, which is the one
	// thing in this file that must not be forgeable by its own content.
	record(step, detail = {}) {
		this.seq += 1;
		const line = { seq: this.seq, ts: this.now(), step,
		               detail: this.scrubDeep(redact(detail)) };
		appendFileSync(this.path, `${JSON.stringify(line)}\n`);
		return line;
	}
}
