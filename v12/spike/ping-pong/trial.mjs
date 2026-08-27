// SPIKE ONLY — W17110. The in-container half of one trial, for either provider.
//
// ONE FILE FOR BOTH PROVIDERS, on purpose. The ruling asks the experiment to
// compare Claude and Codex "at the wrapper boundary", and a comparison is only
// worth anything if the outer shape is the same on both sides. What differs is
// the argv this builds and the runtime it spawns; everything around that —
// where input comes from, what a result looks like, when the completion signal
// appears — is identical.
//
// It is NOT the worker-control protocol. There is no framed channel, no
// manifest, no assignment identity. W6633 owns that and this must not be
// mistaken for it.

import { spawn } from "node:child_process";
import { createHash } from "node:crypto";
import { readFile, rename, writeFile } from "node:fs/promises";

const INPUT = "/input/input.json";
const OUTPUT_ROOT = "/output";
const OUTPUT = `${OUTPUT_ROOT}/output.json`;

// The agent may take a while to answer, and a trial that hung would be a trial
// nobody can read a result from. Bounded here rather than left to the operator.
const DEADLINE_MS = Number(process.env.SPIKE_DEADLINE_MS ?? 240000);

// The exact word the trial asks for. The ruling says "an exact textual pong is
// sufficient Work", and exact is the operative part: `not pong` contains the
// word and is not the answer.
const EXPECTED = "pong";

// What a provider failure may say in durable evidence. The ruling allows a
// "redacted failure category" and nothing more, so the raw provider text never
// reaches `output.json`: an authentication error commonly quotes the thing that
// failed to authenticate.
// The exact path this trial mounted the credential at. The classifier below
// needs it to tell "a write was denied" from "a write to THE CREDENTIAL was
// denied", and those are two different claims.
const CREDENTIAL_PATH = process.env.SPIKE_CREDENTIAL_PATH ?? "";

// A WRITE DENIED SOMEWHERE IS NOT A WRITE DENIED HERE.
//
// W17110's ninth review [P1], and it is the eighth review's rule applied to my
// replacement for the thing the eighth review removed. `EACCES`, "permission
// denied" and "cannot write" can name the input root, the output root, HOME,
// or any path the runtime touched. They establish a write-denied RESULT and
// nothing about what was being written to.
//
// So causation is earned only when the engine's own message names the exact
// path this trial mounted the credential at. Anything else is descriptive.
const WRITE_DENIED =
  /(read-only file system|erofs|eacces|permission denied|cannot write|failed to (write|save|persist))/i;

function writeDeniedCategory(text) {
  // PER DIAGNOSTIC, NOT PER RUN. W17110's tenth review [P1]: this tested the
  // whole of stdout and stderr joined together, so a credential path mentioned
  // in ONE line and an unrelated write denial in ANOTHER combined into a
  // causal claim neither line makes. Two facts that never met still read as
  // one.
  //
  // A message is the unit that carries a claim. The denial and the path have
  // to be in the same one, and anything else is the conservative category.
  let denied = false;
  for (const line of String(text).split("\n")) {
    if (!WRITE_DENIED.test(line)) continue;
    denied = true;
    if (CREDENTIAL_PATH && line.includes(CREDENTIAL_PATH)) {
      return "credential-write-denied";
    }
  }
  return denied ? "write-denied" : null;
}

const CATEGORIES = [
  // ORDERED. `credential-expired` DESCRIBES what was seen and claims no
  // mechanism -- which is what the eighth review's finding was about, and the
  // ninth review's finding is the same rule one layer further in.
  [/oauth.*(expired|refresh)|(expired|refresh).*oauth|token (has )?expired|refresh token/i,
   "credential-expired"],
  [/not *logged *in|unauthor|invalid api key|authentication|401|403|credential|api key/i,
   "authentication"],
  [/quota|rate.?limit|429|billing|insufficient|credit/i, "quota"],
  [/enotfound|econnrefused|etimedout|network|dns|proxy|tls|certificate/i,
   "network"],
  [/not found|command not found|enoent|cannot find module/i, "packaging"],
  [/timed out|deadline/i, "timeout"],
];

function category(text) {
  // A DENIED WRITE WINS, in either form, and this ordering was itself a defect
  // the controls caught: `EACCES: permission denied, open '.../.credentials
  // .json'` contains the word "credential", so with the broader list checked
  // first it classified as `authentication` -- naming the wrong failure
  // entirely, and doing it most confidently in the case that mentions the
  // credential.
  //
  // A write that was refused is a concrete thing that happened. Whatever else
  // the wording resembles, that is what to report.
  const denied = writeDeniedCategory(text);
  if (denied) return denied;
  for (const [pattern, name] of CATEGORIES) {
    if (pattern.test(text)) return name;
  }
  return "unrecognized";
}

// THE EXPECTED ANSWER, AS A DIGEST. This is what lets the host recompute the
// verdict without a single byte of provider text crossing the boundary: the
// container publishes the digest of what the agent actually said, the host
// compares it with the digest of the word that was asked for, and neither
// needs to see the other's plaintext.
function digestOf(text) {
  return `sha256:${createHash("sha256").update(text, "utf8").digest("hex")}`;
}

const RUNTIMES = {
  // Headless, one prompt, one answer. `--print` is the non-interactive mode;
  // the permission mode is the most restrictive one that still lets the model
  // answer a question, because this trial asks it to say a word and nothing
  // else.
  claude: (prompt) => ({
    command: "claude",
    argv: ["--print", "--permission-mode", "plan", prompt],
  }),
  codex: (prompt) => ({
    command: "codex",
    argv: ["exec", "--skip-git-repo-check", "--sandbox", "read-only", prompt],
  }),
};

function ran(command, argv) {
  return new Promise((resolve) => {
    const child = spawn(command, argv, {
      // THE CONTAINER'S REAL HOME, inherited rather than replaced.
      //
      // This first pointed HOME at a fresh `mkdtemp` under /tmp, on the
      // reasoning that a runtime should get scratch space of its own. The
      // Codex trial refused it outright -- it will not place helper binaries
      // under a temporary directory -- and that is a WRAPPER-BOUNDARY FACT
      // worth keeping rather than a nuisance to work around: a provider
      // runtime has opinions about where its own state may live, and a
      // container that invents one is a container it will not run in.
      //
      // The credential provider is mounted read-only at `$HOME/.claude` or
      // `$HOME/.codex`, which is where each runtime already looks.
      env: { ...process.env },
      stdio: ["ignore", "pipe", "pipe"],
      // ITS OWN PROCESS GROUP, so the deadline below can end the whole tree.
      // The Codex trial is what taught this: a provider CLI that spawns a
      // child of its own outlives a signal sent to the parent alone.
      detached: true,
    });
    let out = "";
    let err = "";
    let settled = false;
    const finish = (status) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ status, stdout: out, stderr: err });
    };
    const timer = setTimeout(() => {
      err += "\nspike: deadline reached";
      try {
        // The GROUP, not the process. Killing `codex` alone left its child
        // holding the pipes open.
        process.kill(-child.pid, "SIGKILL");
      } catch {
        child.kill("SIGKILL");
      }
      // AND SETTLE ANYWAY, on a short grace. `close` waits for every stdio
      // handle to reach EOF, and a grandchild that inherited them can hold
      // that open for ever -- which is exactly how the first Codex run hung
      // past its own deadline with nothing published. A trial that cannot end
      // is worse than one that fails: the operator has nothing to read either
      // way, and no reason to stop waiting.
      setTimeout(() => finish(null), 5000);
    }, DEADLINE_MS);
    child.stdout.on("data", (chunk) => { out += chunk; });
    child.stderr.on("data", (chunk) => { err += chunk; });
    child.on("error", (failure) => {
      err += `\n${failure}`;
      finish(null);
    });
    // BOTH, and `exit` is the one that always arrives: it fires when the
    // process ends, where `close` waits for the pipes as well.
    child.on("exit", (status) => setTimeout(() => finish(status), 250));
    child.on("close", (status) => finish(status));
  });
}

// PUBLISHED LAST AND ATOMICALLY, which is the one thing this spike takes
// wholesale from the reviewed contract. The presence of `output.json` under its
// final name is the completion signal, so a half-written one under that name is
// indistinguishable from a finished trial.
async function publish(document) {
  const staged = `${OUTPUT}.publishing`;
  await writeFile(staged, `${JSON.stringify(document, null, 1)}\n`, "utf8");
  await rename(staged, OUTPUT);
}

async function main() {
  const provider = process.env.SPIKE_PROVIDER;
  const build = RUNTIMES[provider];
  if (!build) {
    console.error(`spike: SPIKE_PROVIDER is one of ${Object.keys(RUNTIMES)}`);
    return 2;
  }

  let request;
  try {
    request = JSON.parse(await readFile(INPUT, "utf8"));
  } catch (failure) {
    console.error(`spike: ${INPUT} is not a readable request: ${failure}`);
    return 2;
  }
  const { correlation_id: correlation, request: asked } = request;
  if (typeof correlation !== "string" || typeof asked !== "string") {
    console.error("spike: the request carries correlation_id and request");
    return 2;
  }

  const started = new Date().toISOString();
  const { status, stdout, stderr } = await ran(...Object.values(build(asked)));
  const answer = stdout.trim();

  // AN ALLOWLIST, NOT A REDACTION. W17110's first review [P0], and it is right
  // in a way the earlier version could not be patched into: the rule is not
  // "remove the token spellings I recognise", it is that no credential may
  // enter a result, an evidence file or a log at all. A real agent HOLDS the
  // mounted credential and can emit arbitrary stdout; a prompt asking for one
  // word is not a non-disclosure boundary, and a heuristic over provider text
  // is a guess about text an adversary — or an ordinary bad day — controls.
  //
  // So no provider text is published. What crosses is: the identities this
  // trial was given, the exit state, a DIGEST of the answer, its length, and
  // on failure one member of a closed category vocabulary. Every one of those
  // is a fact this program computed rather than a string the provider chose.
  //
  // THE CORRELATION IDENTITY IS CARRIED, NOT RE-DERIVED. It came in on the
  // request and goes out unchanged; that is the whole point of the shape.
  const document = {
    spike: "w17110-ping-pong",
    provider,
    correlation_id: correlation,
    started_at: started,
    finished_at: new Date().toISOString(),
    exit_status: status,
    // The host recomputes the verdict from this. `sha256("pong")` is a
    // constant it can derive for itself, so an exact match is decidable on
    // the host without the host ever seeing what was said.
    result_digest: digestOf(answer),
    result_bytes: Buffer.byteLength(answer, "utf8"),
    stderr_bytes: Buffer.byteLength(stderr, "utf8"),
  };
  if (status !== 0 || digestOf(answer) !== digestOf(EXPECTED)) {
    // A CLOSED VOCABULARY. `category` matches provider text against fixed
    // patterns and returns one of a fixed set of words; the text it matched
    // is not kept.
    document.failure_category = category(`${stderr}\n${answer}`);
  }
  await publish(document);
  console.error(`spike: published ${OUTPUT} (${provider}, exit ${status})`);
  return status === 0 && document.result_digest === digestOf(EXPECTED)
    ? 0 : 1;
}

main().then((code) => process.exit(code), (failure) => {
  console.error(`spike: ${failure}`);
  process.exit(2);
});
