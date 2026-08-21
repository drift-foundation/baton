// W99: one fresh, private quarantine directory per configuration.
//
// The restart-durable approval fence defaults beside the event socket, so
// every suite whose config points at `/tmp/...` would otherwise share one
// directory — and the first test that quarantines a thread would fence
// every later test using the same server/thread pair. The isolation is
// the point of the fence, not an artefact of the tests: a real deployment
// has exactly one dispatcher runtime directory, and these give each
// scenario its own.
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

export function freshQuarantineDir() {
  return mkdtempSync(join(tmpdir(), "codex-quarantine-test-"));
}
