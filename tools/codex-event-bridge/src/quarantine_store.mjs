import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, readdirSync, renameSync, writeFileSync } from "node:fs";
import { join } from "node:path";

/** Whether a marker instant can actually be READ OUT LOUD later.
 *
 *  W99 review round 5: `Number.isFinite` is not that test. Restoration
 *  formats the instant with `new Date(since).toISOString()`, and a
 *  finite value outside Date's representable range — `Number.MAX_VALUE`
 *  in a hand-edited or partially written marker — passes `isFinite` and
 *  then throws `RangeError` inside `start()`, taking down every healthy
 *  target in the deployment. Classifying with the SAME formatter the
 *  restore uses keeps `present` meaning "this record can be restored",
 *  so a damaged instant stays isolated to its own context exactly like
 *  every other damaged marker.
 */
function usableInstant(value) {
  if (!Number.isFinite(value)) return false;
  try {
    new Date(value).toISOString();
    return true;
  } catch {
    return false;
  }
}

// W99 review P1: the quarantine has to OUTLIVE the dispatcher process.
//
// The confirmed ruling scopes the fence to the managed CONTEXT for the
// remainder of the managed-stack start, and says in as many words that a
// dispatcher-only restart is not recovery because it resumes the same
// configured thread. A fence held only in `EventBridge` state contradicts
// that exactly: stop the dispatcher, start it again against the same
// rendered configuration, and the tainted thread is deliverable again —
// with Baton's level-triggered readiness standing by to reoffer the Work.
//
// The key is the managed context itself, `server + threadId`, and that
// choice is what makes this need no lifecycle cooperation at all:
//
//   - a dispatcher-only restart resumes the SAME thread id, finds the
//     marker, and stays fenced;
//   - a full managed-stack start MINTS A NEW thread id, so the old
//     marker is simply not this context's and the fresh context is
//     clean without anybody deleting anything.
//
// The marker records only what the status row already publishes. Command
// bodies, argv, environment values and filesystem operands never reach it,
// for the same reason they never reach an incident.
export function quarantineKey(serverName, threadId) {
  return createHash("sha256")
    .update(`${serverName}\u0000${threadId}`)
    .digest("hex")
    .slice(0, 32);
}

export class QuarantineStore {
  constructor(directory, logger = console) {
    this.directory = directory;
    this.logger = logger;
  }

  #path(serverName, threadId) {
    return join(this.directory, `${quarantineKey(serverName, threadId)}.json`);
  }

  /** What this context's marker says: `absent`, `present`, or `damaged`.
   *
   *  W99 review round 3: `damaged` is NOT `absent`, and the difference
   *  is the whole safety property. A marker AT THIS EXACT KEY is
   *  positive evidence that the context was quarantined. Losing its
   *  diagnostic payload destroys what we knew about WHY; it is not
   *  proof that the persistent agent context forgot the interrupted
   *  Work. Reading a corrupt file as a clean context fails open — the
   *  restarted dispatcher delivers on the tainted thread — which is the
   *  exact outcome the fence exists to prevent.
   *
   *  Only `ENOENT` is a clean context. Everything else — a parse error,
   *  a permission error, a directory where a file belongs, or an instant
   *  the restore could not format — is damaged and fails closed. */
  load(serverName, threadId) {
    let raw;
    try {
      raw = readFileSync(this.#path(serverName, threadId), "utf8");
    } catch (error) {
      if (error.code === "ENOENT") return { state: "absent" };
      return { state: "damaged", reason: error.message };
    }
    try {
      const record = JSON.parse(raw);
      if (!record || typeof record !== "object" || Array.isArray(record)) {
        throw new TypeError("not a JSON object");
      }
      if (!usableInstant(record.since)) {
        throw new TypeError("no usable `since` instant");
      }
      return { state: "present", record };
    } catch (error) {
      return { state: "damaged", reason: error.message };
    }
  }

  /** Copy damaged marker bytes aside before a well-formed one replaces
   *  them, so the corruption stays inspectable.
   *
   *  Best effort by design: preserving evidence must never cost the
   *  fence. A failure here is logged and the restore continues, because
   *  a readable marker at the live key matters more than the bytes that
   *  could not be parsed anyway. */
  preserveDamaged(serverName, threadId) {
    const source = this.#path(serverName, threadId);
    const kept = `${source}.damaged`;
    try {
      copyFileSync(source, kept);
      return kept;
    } catch (error) {
      this.logger.warn(
        `could not preserve the damaged quarantine marker for `
        + `${serverName}/${threadId}: ${error.message}`);
      return null;
    }
  }

  /** Persist one quarantine. Returns whether it is now durable.
   *
   *  Synchronous and rename-committed on purpose. This runs inside the
   *  server-request handler, before the denial goes out, so the fence is
   *  on disk before anything asynchronous can let another Work in. A
   *  failure is loud and returns false — the in-process fence still
   *  holds for this process, and the caller publishes that the fence is
   *  NOT restart-durable rather than implying it is. */
  save(serverName, threadId, record) {
    const target = this.#path(serverName, threadId);
    const temporary = `${target}.${process.pid}.tmp`;
    try {
      mkdirSync(this.directory, { recursive: true, mode: 0o700 });
      writeFileSync(temporary, `${JSON.stringify(record, null, 2)}\n`,
                    { mode: 0o600 });
      renameSync(temporary, target);
      return true;
    } catch (error) {
      this.logger.error(
        `the quarantine for ${serverName}/${threadId} could NOT be persisted `
        + `to ${this.directory}: ${error.message}. The fence holds in this `
        + `process only — restarting the dispatcher would clear it, so stop `
        + `and start the managed stack rather than relaunching the dispatcher.`);
      return false;
    }
  }

  /** Marker keys present on disk. Diagnostics only. */
  keys() {
    try {
      return readdirSync(this.directory)
        .filter((name) => name.endsWith(".json"))
        .map((name) => name.slice(0, -5));
    } catch {
      return [];
    }
  }
}
