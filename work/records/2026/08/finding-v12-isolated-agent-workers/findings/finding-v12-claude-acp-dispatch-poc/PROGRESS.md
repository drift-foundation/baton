# Progress

Implementer-owned. One writer (`baton.claude`).

## Status

**Round 6 — corrections applied, awaiting independent review.** `W76`
was reclaimed 2026-08-21T00:45Z after
`review-2026-08-21T00-38-29Z.md` requested changes, and is being passed
back to `baton.feat` (`rview`) rather than closed.

Both round-5 findings were reproduced by reading the paths before being
fixed. The suite is 59 tests (was 55, 50, 44, 35, 27). Fresh packs
`proof-r6-1` and `proof-r6-2`.

**Noted, not acted on:** the round-5 handoff says W415 is the
higher-priority blocker and should be addressed first. W415 is currently
routed to `baton.bug` — the reviewer's own endpoint — so it is not mine
to claim; W76 was the only actionable item on this participant's
readiness. If W415 should come back to `baton.impl`, it needs rerouting.

**Also noted:** the review records a repository-placement decision
superseding this external root in favour of a self-contained top-level
`v12/` subtree, as a bounded follow-up after technical sign-off. Nothing
in this round moves anything; the external root remains the reviewed
source.

## Where the work lives

- Prototype source: `/home/sl/src/baton-v12-poc` — external, its own
  git repository, its own dependencies, tests, fixtures and runtime
  state. The operator established its baseline at `b0fb0cf`; this
  implementer performed no Git operation of any kind, there or here.
- Evidence packs: `/home/sl/src/baton-v12-poc/evidence/` — read
  `proof-r6-*` for the current prototype; earlier packs are kept because
  they are the evidence for observations recorded here.
  `evidence/README.md` says which round is which and why.
- Reproduce the whole thing: `scripts/run-proof.sh <label>`
- What was copied from Baton v11 and how it was changed:
  `/home/sl/src/baton-v12-poc/PROVENANCE.md`

Within the Baton repository this Work modified exactly one file: this
`PROGRESS.md`. (`PLAN.md` and the review journal are reviewer-owned and
were changed by the reviewer, not by this implementer.) No Baton application, bridge, lifecycle, test, recipe,
release-template or deployment file was touched, and the proof runner
asserts that on every run.

## The question, answered

An operator submits an ordinary Baton Job through the CLI. A trusted
prototype Worker Manager observes it through `wait`, offers it to an
isolated Claude ACP worker, obtains explicit token-bearing consent,
commits the canonical claim, runs the work in a second isolated
container, freezes and independently verifies the result, and returns
the Job for review — **with no Claude process launched or prompted by
hand for that individual Job.** Wall clock, submit to return: 30–55
seconds.

The one lifecycle, as the trace records it
(`evidence/proof-r2-1/traces/*-happy.jsonl`, 82–114 steps):

```
attempt.start -> baton.detail.before -> job.in.read -> input.materialized
-> credential.staged -> offer.minted -> preclaim.container -> preclaim.turn
-> preclaim.quiesced -> preclaim.intent -> token.validated -> baton.claim
-> baton.detail.claimed -> assignment.minted -> worker.container
-> worker.activity* -> worker.turn -> worker.fenced -> input.reverified
-> worker.declared -> result.frozen -> result.checked -> baton.say
-> baton.pass -> baton.detail.after
```

`scripts/run-proof.sh` asserts the load-bearing subset of that ordering
mechanically rather than by inspection:

- `token.validated < baton.claim < assignment.minted < worker.container`
  — **nothing writable exists before the canonical claim commits**, and
  the claim is never reached without a validated token.
- `preclaim.turn < token.validated` — the token is checked only after
  the agent has actually answered.
- `worker.fenced < result.frozen < result.checked < baton.pass` — the
  worker is proven stopped before anything reads its output, and the
  result is validated before the Job is handed on.
- `input.reverified < result.frozen`, with the before/after input
  digests required to be equal.

### Handler, before / during / after

Three separate public reads, not inferences from the claim's own result
(`evidence/proof-r2-1/snapshots/`):

| Moment | phase | handler | route |
| --- | --- | --- | --- |
| before any claim | `queued` | `null` | `poc.job` |
| while claimed | `active` | `poc.claude` | `poc.job` |
| after return | `queued` | `null` | `poc.rview` |

### Isolation, asserted per run

Neither container received the Baton executable, its configuration or
its database — asserted both in code (`runtime.assertNoBatonCapability`,
run before every launch) and against the `docker inspect` mount list in
the evidence. Both containers ran as uid `1000:1000`, with all
capabilities dropped and no new privileges. The execution container's
only writable result destination was `/out`.

The **consent turn** runs in the non-executing ACP `plan` posture on a
read-only root filesystem, with no copy of the Job's input and nowhere
to write a result, and it performed **zero tool calls** while the worker
performed 19–24. Its answer comes back as ACP text and is worth exactly
what the manager's token check says it is worth.

Two residuals are deliberately not claimed away: the credential bind is
writable because the Claude SDK requires a writable config directory,
and network egress to the model provider exists because a model turn
needs it. So the property established is that **a consent turn holds no
Baton capability, touches no Job input or output, executes no tools, and
cannot produce an accepted result or an assignment** — not that it is
physically incapable of writing a byte anywhere.

*Round 1 of this document claimed the stronger, false version. Review
2026-08-20T19:57:54Z caught it; finding 4 in the response below records
what was enforced and what was narrowed.*

### The result is checked independently

The manager never asks the agent whether its own answer was right. It
recomputes the transformation from the same read-only input
(`src/fixture_check.mjs`) and compares structurally. The fixture
exercises four distinct cases on purpose: a plain first-line heading, an
indented heading in a `.txt` file, a file with no heading at all, and a
`##` heading that is not the first line.

Across independent runs from fresh disposable authorities, one round per
review:

| Run | round | status | input digest | output digest | activity |
| --- | --- | --- | --- | --- | --- |
| proof-1 … proof-4 | 1 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 60/44/52/44 |
| proof-r2-1, proof-r2-2 | 2 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 55/44 |
| proof-r3-1, proof-r3-2 | 3 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 57/48 |
| proof-r4-1 | 4 | returned | `4ce540a1c45e…` | **`27b4188118d0…`** | 55 |
| proof-r4-2 | 4 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 47 |
| proof-r5-1 | 5 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 57 |
| proof-r5-2 | 5 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 67 |
| proof-r6-1 | 6 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 62 |
| proof-r6-2 | 6 | returned | `4ce540a1c45e…` | `c3b7d7dcd6f2858f…` | 59 |

**A correction to what earlier rounds claimed here.** Rounds 1–3 said
the output digest was identical across every pack and offered that as
the reproducibility result. Round 4 produced a *different* digest — and
the independent check still passed, because the model wrote the same
JSON with different whitespace:

```
proof-r3-1  420 bytes, one field per line
proof-r4-1  324 bytes, one entry per line
parsed values equal: true
```

`proof-r4-2` then came back to the original digest, so the bytes
genuinely alternate between two formattings run to run.

So the honest statement is the one the contract was always built on:
**the RESULT reproduces; the bytes are not promised.** Eight identical
digests were eight samples, not a property, and presenting them as a
property was over-claiming. This is also the strongest evidence yet for
correction 7 below — a contract requiring byte-identical model output
would have failed this run for a formatting difference while the answer
was exactly right.

### The negative proof

Three cases run on every proof, all against genuine faults rather than
simulated refusals: `expired` mints with a 1 ms lifetime, `replayed`
genuinely spends the token before the turn, and `post-claim` injects a
failure after a real canonical claim (added in round 2 — see finding 5
below, which covers what it asserts).

The two token cases:

In both cases the pre-claim turn **ran, accepted, and returned a
well-formed token-bearing intent**, and the manager refused it anyway.
That ordering matters: it proves the fence is the token check and not
the absence of an agent. Asserted per run, from the trace and from a
fresh public read:

- no `baton.claim`, no `assignment.minted`, no `worker.container`, no
  `result.frozen`, no `baton.pass`;
- the refusal is recorded with the exact expected reason;
- the Job is left `phase: queued`, `handler: null`, `ready: true`, at
  its original route — available for a fresh offer.

Unit tests cover the refusals the end-to-end proof cannot reach cheaply:
forged tag, unknown handle, misbound Work/participant/runtime-attempt,
absent token, a confident `"working"` reply carrying nothing, and the
rule that a *refused* token is not thereby marked spent — plus, from
round 2, every refusal shape of the quiescence fence, input containment,
declaration binding, the consent posture, and both compensation
outcomes. 35 tests, all passing, run as the first step of every proof.

## Assumptions that held

1. **A local Claude ACP worker runs fully containerized.** `docker run
   -i` speaking ACP over stdio to `@agentclientprotocol/claude-agent-acp`
   in `node:24-slim`, with the adapter tree mounted read-only. No image
   build was required.
2. **v11's ACP session discipline transfers unchanged.** Capability
   negotiation before session use, exact-permission-mode enforcement
   with no fallback, permission-request-as-policy-failure, and v11's
   SETUP deadlines all work identically when the subprocess is a
   container. See `PROVENANCE.md`. *Round 3 correction: this sentence
   used to say "supervised deadlines", which read as turn supervision.
   v11 supervises setup only and races a prompt against the agent's
   death alone. The turn deadline this prototype now has is an addition,
   not something inherited — see finding 1 below.*
3. **The deployed v11 executable is a sufficient black-box boundary.**
   Every coordination act — `wait`, `detail`, `resolve`, `claim`,
   `say`, `pass`, `bind`, `reroute`, `create` — went through the
   documented CLI/JSON surface. No SQLite file was opened by this
   prototype or by any model in it, and no protocol state was
   reconstructed by hand.
4. **Typed directory input works as a digest-bound read-only mount.**
   The operator-declared digest, the digest of what the worker actually
   saw, and the digest after execution were equal in every run.
5. **ACP `session/update` notifications are the natural activity
   channel.** Agent messages and tool calls arrive as structured
   updates and required no separate reporting mechanism inside the
   container.
6. **A claim-before-execution boundary is enforceable from outside
   Baton.** The manager alone holds coordination capability; the worker
   has none, by construction rather than by policy.

## Assumptions that failed or need revision

These are the corrections this proof exists to produce. Each is a
proposal to W2, not a decision.

1. **A long opaque consent token cannot travel through a model
   channel.** *Observed 2026-08-20, run `proof-2` first attempt.* The
   first design had the agent echo a 402-character signed-payload token
   verbatim. An otherwise perfect pre-claim turn transcribed it
   incorrectly and the attempt was refused as `forged`. The fence
   behaved exactly right — nothing was claimed, nothing ran, the Job
   stayed available — but refusing honest consent because a model
   miscopied a long string is a **contract defect, not a security
   result**. Revised in the prototype to a 39-character opaque handle
   (`<id>.<tag>`) with the bound payload held manager-side; surrounding
   whitespace is normalised away, which cannot turn an invalid tag
   valid. Four clean runs since. **v12's consent token must be short,
   opaque, and carry no binding information.** A structural mismatch
   diagnostic (`describeTokenMismatch`) is now recorded on every
   signature refusal, because "the signature does not verify" cannot
   distinguish a forgery from a typo and those want opposite fixes.
2. **Worker credential delegation is unsolved and is the largest gap.**
   The prototype hands the worker a **copy of the operator's own Claude
   OAuth credential**. A refresh inside the container would mint a
   replacement refresh token and silently invalidate the operator's, so
   staging refuses unless the access token has ≥15 minutes of life left
   — the worker therefore never has a reason to refresh. That is a
   **stated stopgap, not a design.** v12 must issue a scoped,
   short-lived, worker-specific credential. Nothing about this proof
   depends on the stopgap surviving.
3. **Non-root execution is load-bearing, not a preference.** A worker
   container running as root is **not offered** the `bypassPermissions`
   session mode by the adapter, and the session fails closed. The
   worker must run as a non-root uid; `runtime.user` refuses anything
   that is not `uid:gid`. v12's worker-control contract should state
   this as a requirement with its reason.
4. **`handler` is an object in the v11 projection, not a string.** It
   is `{team, member, participant}` or `null`. Reading it as a string
   yields `[object Object]`, which looks populated. This was caught by
   an assertion, not by inspection. Any v12 consumer of the projection
   should go through one accessor. *This is a documented shape, not a
   Baton defect.*
5. **Baton constrains where a Job's typed input can live, and who may
   put it there.** Two rules interact: every binding must match
   `work/records/YYYY/MM/<stable-record>`, and `bind` requires the
   **resolved route handler**. An operator therefore cannot prepare
   typed input for a Job already routed to the worker queue. The
   prototype models the real move — submit at the operator's own
   endpoint, bind there, then `reroute` the unclaimed Job onto the
   worker queue — which is exactly what `reroute` is documented for.
   **v12's Job-intake contract must either adopt this three-step shape
   or carry typed input somewhere other than a binding.** *Both rules
   are deliberate; neither is a defect.*
6. **Evidence redaction must be fragment-aware.** A streamed ACP reply
   arrives as many short chunks. No individual chunk of a token is
   recognisable as a credential by name or by shape — while their
   concatenation is the whole thing. Name- and shape-based redaction
   both let the first design's token through into the trace intact.
   The trace now scrubs by fragment against registered secrets, and the
   proof runner asserts that **no 16-character fragment** of the live
   token survives. v12's trace contract should require this; it is not
   something an implementation will get right by default.
7. **Byte-identical model output should not be contracted.** The
   prototype validates the *parsed* result against an independent
   recomputation and digest-binds the *bytes*. Requiring byte equality
   would turn a formatting difference into a lifecycle failure while
   adding nothing. Two further rules earned their place the same way:
   a result containing anything the Job did not declare is refused, and
   an entry carrying an undeclared field (a plausible `"confidence"`,
   say) is a mismatch rather than a bonus.

### Two smaller observations

- **The worker's system posture is not fully clean.** In one run the
  worker volunteered a note about unrelated host MCP connectors needing
  authorization, despite being started with `mcpServers: []`. Harmless
  here, and it did not affect the result, but v12 should pin what
  system context a worker turn actually inherits.
- **A trace payload must not be able to overwrite the trace's own
  ordering field.** Baton results routinely carry their own `seq`;
  spreading a recorded payload into the trace line let one silently
  replace the monotonic counter — in a file whose entire purpose is
  establishing order. Detail is now nested. Both this and the
  fragment-redaction gap are regression-tested.

## Stop conditions

None were triggered. The proof required no change to Baton source, no
direct SQLite access, no production mailbox, no manual per-Job
prompting, no TUI work, no embedded long-lived credential (the staged
credential is a runtime copy, guarded and documented above), and no
weakening of the claim-before-execution boundary.

**No Baton defect was encountered.** The two v11 behaviours that shaped
the prototype's design — the canonical binding-path shape and `bind`
requiring the resolved route handler — are deliberate documented rules,
and the prototype obeys them rather than routing around them. Per
`AGENTS.md` there is accordingly no defect finding to log; had there
been one, it would have been filed before any workaround.

## Acceptance boundary

| # | Requirement | Where it is shown |
| --- | --- | --- |
| 1 | no prototype product-source edits in the Baton repository | `evidence/*/baton-repo-status.txt`, asserted per run |
| 2 | external prototype inspectable from a clean baseline | `/home/sl/src/baton-v12-poc` @ `b0fb0cf`, `PROVENANCE.md` |
| 3 | an ordinary Job naturally wakes Claude, no per-Job launch | `evidence/*/manage-happy.json`, happy-path trace |
| 4 | manager alone holds Baton; claim precedes writable execution | ordering assertions; `assertNoBatonCapability` |
| 5 | typed input verified and immutable; output separate, declared, frozen, validated, digest-bound | `input.materialized` / `input.reverified` / `result.frozen` / `result.checked`; `evidence/*/manifests.txt`. Round 3: the declared result is the pinned **directory**, asserted per run |
| 6 | expired and replayed tokens start nothing and publish nothing | `evidence/*/manage-{expired,replayed}.json` and their traces |
| 6b | a post-claim fault releases the claim rather than stranding it | `evidence/proof-r2-*/manage-postclaim.json` and its trace |
| 7 | the Job returns for review with sufficient public state | `baton.say` recap + `baton.pass`; after-return snapshot |
| 8 | a fresh disposable authority reproduces the same lifecycle result | fourteen runs; the independently recomputed RESULT matches every time (the bytes do not — see the table) |
| 9 | an explicit go / revise / no-go, without representing prototype code as adopted | this file |

## Evidence index

Per pack, under `/home/sl/src/baton-v12-poc/evidence/<label>/`:

- `prerequisites.txt` — host, Docker, Node, Baton binary and commit,
  ACP adapter, worker image digest
- `unit-tests.txt` — the 59 fail-closed tests
- `traces/*.jsonl` — chronological traces: happy path and both negatives
- `snapshots/*.json` — Handler before claim, while claimed, after return;
  and the post-refusal state of each fenced Job
- `envelopes/` — `job.in`, `offer` (token stripped), `assignment`
- `results/` — the frozen `index.json` and the `result` envelope, with
  input/output manifests, container identity and termination
- `manifests.txt`, `independent-check.txt`, `baton-repo-status.txt`

No credential material appears in any pack; the runner greps for it and
fails the run if it finds any.

## Response to review 2026-08-20T19:57:54Z

Every finding was reproduced first. The reviewer's three code-level
reproductions all fired exactly as described.

### 1 (P1) — a failed quiescence check became evidence — **fixed**

Confirmed: both call sites did
`awaitQuiescence(...).catch(error => ({error: error.message}))` and
carried on, so an unprovable fence was recorded and stepped over. The
execution path then read and froze a writable directory whose writer
might still have been alive.

`container.assertQuiesced` now decides, and it refuses everything that
is not an unambiguous clean self-termination: an inspection error,
`running` not `false`, a manager-forced stop, or a non-zero exit. A
forced stop is refused specifically because it cannot be distinguished
from a kill in the middle of a write.

It is called **outside** the `finally` blocks — inside, a throw would
mask the turn's own failure — and before any boundary: for consent,
before the intent is even parsed, let alone claimed; for execution,
before the output directory is read. Both refusals are `FenceHeld`, so
the attempt ends the same way a token refusal does.

Regression `R1` covers all five refusal shapes and the clean case. The
proof runner now asserts `error` absent, `running: false`,
`stopped_by: "self"` and `exit_code: 0` for both containers on every
run, rather than the weaker running/exit pair it checked before.

### 2 (P1) — typed input could escape its bound record — **fixed**

Confirmed, and this was the most serious of the five: a record-local
`input` symlink pointing at an outside directory produced a valid
manifest containing that directory's `secret.txt`. Every downstream
digest then faithfully described content the Job was never entitled to.
`cpSync(..., {dereference: true})` is what turned an untrusted
descriptor into host-file disclosure.

New `src/input_source.mjs` establishes containment before anything is
copied:

- `resolveInputSource` refuses an absolute path, any `..` segment, a
  resolved path outside the record, a **symlink at the source root**,
  and a source that is not a directory — then re-checks containment on
  the `realpath` of both sides, because the lexical check is exactly
  what the root symlink walks past.
- `copyTreeStrict` replaces `cpSync` and never follows a link: any
  symlink, socket or device below the source is refused rather than
  skipped. Skipping would silently produce a snapshot that does not
  match the Job's declared input.

The same strict copy now freezes the worker's output, which was writable
by the worker and could equally have had a link planted in it.

Regressions `R2` and `R2b` cover traversal, absolute paths, the
root-directory symlink the reviewer built, a nested symlink, a
non-directory source, and a plain tree still copying exactly. The trace
records `followed_links: false` and the proof runner asserts it.

### 3 (P1) — `job.out` was parsed but not bound — **fixed**

Confirmed: `{"work":"W999","results":[]}` was accepted and collection
proceeded against the manager's own hard-coded path. The declaration was
decoration.

`declarationProblems` now requires an exact match against the assignment
and the offer: this Work, the same number of results, and each result's
`name`, `type` and `path` positionally identical, with duplicate names
refused. A mismatch is `FenceHeld("declaration-mismatch")` **before**
any output is read.

The reviewer's second gap in the same finding — `diffIndex` rejecting
undeclared fields inside an entry but not at the top level — is closed
too. It was the same exactness argument applied at one level and not the
other.

Regressions `R3` (including the reviewer's exact declaration) and `R3b`.

### 4 (P1) — the "read-only pre-claim" claim was false — **enforced *and* narrowed**

The reviewer is right, and this one was a false statement in this
document rather than a bug in the code. The consent container had a
writable credential bind, a writable tmpfs, Docker's writable container
layer, egress, and the **same `bypassPermissions` posture as the
worker**. The absence of a result mount was doing all the work, and the
sentence claimed far more than that.

The review offered either enforcing a genuinely non-executing surface or
narrowing the claim. Both were done, because neither alone is honest.

*Enforced.* Consent and execution are now separate postures, and
`config.mjs` refuses a document that gives them the same one. Consent
runs in the ACP **`plan`** mode — the agent does not execute tools at
all — required exactly, with no fallback, on a read-only root
filesystem, with `--cap-drop ALL` and `--security-opt
no-new-privileges`. `assertPreClaimPosture` checks each clause, and
additionally refuses any `/in` or `/out` mount even read-only: consent
is decided from the offer, never from the Job's data.

*Measured.* In `proof-r2-1` the consent turn performed **0 tool calls**
and the worker performed 24. The proof runner asserts both, and asserts
the posture flags read back from the runtime rather than from the spec
that was requested.

*Narrowed.* The two residuals are stated wherever the property is
claimed, and not claimed away: the credential bind is writable because
the Claude SDK requires a writable config directory, and network egress
to the model provider exists because a model turn needs it. The property
this prototype establishes is therefore:

> A consent turn holds no Baton capability, touches no Job input or
> output, executes no tools, and cannot produce an accepted result or an
> assignment. Only a validated token can.

That sentence — not the old one — is what `README.md`,
`src/runtime.mjs`, the consent prompt and this document now say. The two
statements are not preserved as equivalents.

### 5 (P2) — a post-claim failure stranded the Handler — **fixed, bounded**

Confirmed: `dispatch` caught post-claim failures, recorded
`attempt.error`, removed containers, and left the Job `active` under
`poc.claude` while reporting the attempt over. Exactly the stranding
`docs/EFFECTIVE-BATON.md` warns about.

The manager now compensates for precisely what it committed: on any
failure after a successful claim and before a successful pass, it issues
one `release`, compare-and-swapped against the claimant it knows it
committed, returning the Job to the availability it had before the
offer. This is deliberately **not** a recovery subsystem — one bounded
act, no retries, no re-offer.

Two new terminal statuses make the outcome unambiguous, because the
review's real point was that a failure must not look like a clean end:

- `compensated` — the claim was committed and then released; the Job is
  offerable again.
- `stranded` — the release itself failed. The canonical Handler is still
  held, the trace says so loudly, and `bin/v12-poc manage` exits
  non-zero. A stranded Job is a real operational state and is never
  reported as success.

Proving this needed a failure after a real canonical claim, so
`--fault post-claim` injects one; there is no honest way to observe the
path otherwise. It is now a **third negative case in every proof run**,
asserting that the claim really was committed, the fault landed after
it, the release succeeded, nothing was passed on or frozen, and the Job
is `queued`/unclaimed/`ready` at its original route.

Regression `R5` covers both the compensated and stranded outcomes with a
stubbed authority.

### Also corrected this round

- **A flaky test of my own.** The round-1 test asserting the short
  handle carries no binding information compared it against 2-character
  values like `"W2"` and `"d0"`; a 39-character token containing one by
  chance is a coin flip, and it failed once during this round. Now it
  binds long distinctive values. Verified stable over eight consecutive
  runs.
- **Container hardening is captured while the container exists.**
  `readonly_rootfs`, `cap_drop` and `security_opt` are read back at
  inspect time, because containers are removed at the end of an attempt
  and the evidence could not otherwise answer the question later.

### Three more corrections proposed to W2

Additions to the seven above, all from this round:

8. **A worker-control contract must say what "stopped" means.** "The
   container is no longer running" is not sufficient: a manager-forced
   stop and a clean self-exit are different facts, and only one of them
   licenses reading a result. v12 should require a *positive* clean
   termination before collection, and treat an unprovable one as a
   failed attempt rather than a recorded anomaly.
9. **The IN contract must treat the input descriptor as untrusted.**
   Containment belongs in the contract, not in an implementation's good
   manners: real-path containment inside the bound record, no link
   following, and refusal — not silent skipping — of anything that is
   not a regular file or directory.
10. **The state machine must name a post-claim compensation
    obligation.** Whatever commits a claim owes either a handoff or a
    release. v12 should also distinguish "compensated" from "stranded"
    as terminal attempt states, because an implementation that cannot
    say which one happened will report both as failure and leave the
    queue blocked.

## Response to review 2026-08-20T21:07:20Z

All four reproduced first.

### 1 (P1) — ACP turns had no deadline and could hold a claim forever — **fixed**

Confirmed. `setupTimeoutMs` supervises initialize / session / mode and
stops there; `prompt()` raced only the container's death. A live but
silent agent kept that promise pending forever, and with it the
`finally`, the fence, compensation and the return — so the canonical
Handler was held indefinitely by a turn nobody was watching. The
reviewer is also right that `PROVENANCE.md` and `PROGRESS.md` described
setup-only supervision as turn supervision; both are corrected above and
in `PROVENANCE.md`, and this is an addition to what v11 does, not
something inherited from it.

Both turn classes now carry an explicit **manager-owned** deadline,
required by config with no default —
`preclaim_turn_timeout_ms` and `execution_turn_timeout_ms` — because a
turn with no deadline can hold a claim for as long as the agent stays
quiet, and that is not a thing to fall back to silently. `TurnTimeout`
is its own error type: "the agent went quiet" and "the agent failed"
need different handling downstream, since the first leaves a container
that is still alive.

Regressions `R2-1`: a session constructed without a positive deadline is
refused outright; a prompt that never resolves rejects within the
deadline instead of hanging; a prompt that answers in time is untouched.

### 2 (P1) — compensation released before uncertain execution was dead — **fixed**

Confirmed, and this was the sharpest of the four. `compensate()` ran in
the `catch`; container removal was in the `finally` **after** it; and
`remove()` swallowed every error. So a fence that could not be
established released the Work while the previous execution container may
still have been running — exactly the overlap the claim boundary exists
to prevent. The per-attempt output mount bounds the damage without
making two live executions of one Job safe.

Reaping now happens **first**, and it establishes absence positively:
`removeAndVerify()` removes and then requires `docker inspect` to answer
*no such object*. A daemon that cannot answer is not evidence of
absence, so anything else reports `gone: false`.

The claim is released only when the execution container is proven gone.
When it is not, the manager **keeps the claim** and reports `stranded`,
recording `compensation.withheld` in the trace. Holding a claim nobody
is progressing is a visible loose end; advertising Work whose worker
might still be alive is an invisible one, and the visible failure is the
better one.

The consent container is reaped too but does not gate anything — a
consent turn holds no claim and writes nothing, so a lingering one is
untidy rather than unsafe, and the trace says which is which.

Regressions `R2-2`: absence proven only by an explicit *no such object*;
an unprovable reap withholds the release, strands the attempt, and
`compensate()` is **not even called**; a proven reap releases, with the
order asserted as `["reap", "release"]`. The proof runner now asserts
`containers.reaped` precedes `baton.release` in the live post-claim
case.

### 3 (P1) — the capability fence was lexical and a symlink walked past it — **fixed**

Confirmed against `assertNoBatonCapability` directly: a source that is a
symlink to `/home/sl/baton-v11.8835cd5` was accepted, and Docker
resolves bind sources, so the container would have got it.

Every mount source is now canonicalized with `realpath` before
comparison, and forbidden roots are canonicalized too — with their
literal spelling still compared, so a root that does not exist on this
host today is not silently dropped from the fence. A source that cannot
be canonicalized is **refused as ambiguous** rather than assumed safe,
and the refusal names what the path really is so the operator is not
left comparing two strings that look unrelated.

Regression `R2-3` covers the reviewer's exact root-symlink case, the
"really at" message, an honest source still passing, and the
unresolvable-source refusal. My own round-2 test had to be corrected as
part of this: it used fictional mount sources, which the strengthened
fence now refuses.

### 4 (P2) — the pinned directory result had become a file — **contract fulfilled**

Confirmed, and this one was mine to own rather than to argue. The bound
finding pins "one typed `directory` input and one declared `directory`
result"; I offered and required `{type: "file", path: "/out/index.json"}`
without saying so. Typed IN/OUT is one of the questions this proof
exists to settle, so quietly treating the two as equivalent was the
wrong move.

I fulfilled the pinned contract rather than asking for a scope revision.
The declared result is now the **directory** `/out`, and the entries it
may contain are declared with it (`entries: ["index.json"]`) so
containment still refuses anything undeclared. The worker prompt says
the result is a directory that must end up containing exactly that and
nothing else, and the declaration it returns is `type: "directory"`.

Regressions `R2-4`: the directory declaration validates, a file
declaration is refused with both the type and the path named, and an
undeclared file inside the result directory is refused. The proof runner
asserts the offered type, path and entries on every run.

Worth recording: the output digest `c3b7d7dcd6f2858f…` is **unchanged**
across the contract change and all eight packs, because the digest was
always over the manifest of the frozen tree. The contract was wrong; the
artifact was not.

### The proof's repository check changed shape

The runner used to assert the whole Baton tree was clean outside this
dossier. That is no longer a property W76 can prove: this checkout now
carries unrelated in-flight Work (`W415`), and a status listing records
that a path changed, never who changed it. It first tripped on
`PLAN.md`, which the **reviewer** had edited.

So the runner now proves what it can — that the proof run mutates
nothing in the Baton repository, by comparing status before and after —
and **reports** the dirty paths verbatim, separating this dossier's from
the rest, rather than asserting authorship it cannot establish. That is
a weaker claim than before and an honest one; W76's implementation is
external, and nothing in it writes to the Baton repository.

### Three more corrections proposed to W2

11. **A worker-control contract must require a turn deadline.** Not a
    default, an operand: an agent turn with no manager deadline can hold
    the canonical Handler for as long as the agent stays silent, and
    setup supervision is not turn supervision.
12. **Releasing a claim must be gated on proven termination.** "A
    removal was issued" is not "the worker is gone". v12 should require
    a positive absence answer before Work is advertised again, and
    should define the terminal state for when that cannot be
    established — the safe outcome is a held claim and a loud report,
    not an available Job.
13. **Capability fences must compare canonical paths.** A container
    runtime resolves bind sources, so a fence that compares spellings
    documents today's configuration rather than enforcing anything.
    Unresolvable sources should be refused, not assumed.

## Response to review 2026-08-20T23:30:47Z

All four reproduced first; two of them straight out of the returned tree.

### 1 (P1) — every attempt left a full OAuth credential on disk — **fixed**

Confirmed immediately: four `mode-0600`, 509-byte
`run/attempts/*/claude-config/.credentials.json` copies, refresh token
included, after the round-3 packs. The reviewer's diagnosis of why it
was missed is also exactly right — the evidence-pack grep scanned
`evidence/<label>`, and the secrets were in `run/attempts/`, which is
where they are actually staged. My cleanup story was "it is a runtime
copy", and that is not a lifecycle.

`disposeCredentials()` now overwrites the bytes and removes the staged
directory, and it runs on **every** path — success, pre-claim failure,
compensated failure — from inside `reap()`, so it is structurally tied
to the containers being gone rather than bolted onto one branch.

It disposes only when **both** containers that mount it are positively
absent; the consent container mounts it too. When absence cannot be
proven the credential is deliberately **kept** and named — in
`credential.retained` and in the `compensation.withheld` record — because
removing a file from under a live process is not cleanup, and an
undisposed secret that is named is recoverable while one quietly assumed
gone is not. The byte overwrite is not claimed as unrecoverability on a
copy-on-write filesystem; it removes the plain copy from the obvious
place.

The proof runner now asserts the **runtime** state, walking
`run/attempts` for any `.credentials.json` and grepping it for
credential material — the check that would have caught this.

Regressions `R3-1`: disposal on the success and failure paths,
idempotence, and the unprovable-reap case retaining loudly.

### 2 (P1) — the production guard missed the live alias — **fixed**

Confirmed, and this one was worse than the review states: `/home/sl/baton-v11`
is a **live symlink** to the production home, it is how the deployment
is conventionally addressed, and my guard accepted it because the
pattern required a dot after `baton-v11`. The prototype could have
attached to the production authority.

The comparison is now on **real paths**: the configured authority is
resolved to its nearest existing ancestor, each forbidden root is
resolved, and containment decides. One rule replaces three patterns and
catches the live alias, a `/tmp` link, and a prototype-root link
alike. A lexical family pattern is kept alongside it so a versioned home
that does not exist yet is still refused rather than being unresolvable
and therefore invisible.

Regression `R3-2` covers the exact live path, the versioned path, a
not-yet-existing versioned home, the config directory, a symlink
resolving into production, and two disposable authorities that must
still pass.

### 3 (P1) — an ambiguous committed mutation was reported wrongly — **fixed**

Confirmed by reading the path, and the reviewer found both directions:
a committed **claim** whose result was lost left `claimCommitted` false,
so nothing reconciled and the Handler stayed held under an `error`
report; a committed **pass** whose result was lost entered compensation,
release refused because the Handler was already gone, and the attempt
reported `stranded` although the Job had reached review.

`pass` now carries an operation id like every other manager mutation,
and both go through one `committed()` helper: attempt, then **replay the
same operation id** (v11 replays the committed result byte-identically),
then — only if even that cannot answer — ask the **public projection**
whether the effect is already present. The predicate is per-mutation:
for a claim, the Handler is me; for a pass, the route is the review
endpoint and the Handler is null. If the effect is absent the failure
stands, and if canonical state cannot be read at all the attempt refuses
to guess.

Regressions `R3-3`: a committed-then-lost claim reconciles, a genuinely
absent effect still fails, a replay that succeeds never reaches the
projection, and a committed-then-lost pass is not called stranded.

### 4 (P2) — the launch used the mutable alias — **fixed**

Confirmed. `assertNoBatonCapability()` resolved for comparison and then
returned the spec unchanged, so Docker got the alias — and my comment
claimed that covered later-retargeted links, which canonical comparison
alone does not do. The comment was the worse half of the defect.

It now returns a spec whose mount sources are the canonical paths that
were validated, and the alias is retained beside them as evidence of
what the configuration named. Docker resolves the source anyway, so a
correct configuration is unaffected and the check-to-launch window is
gone. The comment says what is actually true.

Regression `R3-4` proves the runtime argv contains the canonical source
and **not** the alias.

### Also this round

- **The reproducibility claim in this document was over-stated**, and
  round 4's own run is what exposed it. See the table above: the digest
  changed, the independent check still passed, and the parsed values are
  identical. Corrected.
- The round-3 test scaffolding I left behind (dead imports and a stubbed
  field that did nothing) is removed.

### Three more corrections proposed to W2

Additions to the thirteen above.

14. **Staged worker credentials need a disposal contract, not just an
    injection one.** v12 should require disposal gated on proven
    container absence, and should define the terminal state for a
    credential that could not be disposed — a named retained secret,
    never a silent one. This is the second time a lifecycle in this
    prototype has been half-specified in the same way (the first was
    container removal).
15. **Isolation guards must compare real paths, and act on them.**
    Resolving for a decision and then acting on the alias leaves the
    window open. v12 should require that what was validated is what is
    launched.
16. **Every manager mutation needs an effectively-once identity AND a
    reconciliation rule.** An operation id alone does not settle a lost
    result; the contract has to say which canonical observation proves
    the effect, per verb, because "did my claim commit" and "did my
    handoff commit" are answered by different fields.

## Handoff

`W76` returns to `baton.feat` (`rview`) for independent review. The
prototype is disposable and stays where it is: no production port has
been attempted, and none should be inferred from a passing proof. The
useful output of this Work is the seven corrections above.

## Response to review 2026-08-20T23:56:14Z (round 4)

### 1 (P1) — a successful handoff could retain the credential — **fixed**

Confirmed by reading the path. `reap()` returned `{gone: true}` from the
**worker alone** while disposal correctly required **both** containers,
so a consent container whose absence could not be proven left the
credential on disk — and the attempt still finished `returned`, exit
zero. There is no compensation record on that path, because nothing
failed. Round 4 of this document claimed a retained credential is named
as a recoverable terminal condition; on that path it was a trace line
under a clean success.

Two changes, because one would not have been enough:

- **Cleanup is now part of the success boundary.** The reap and disposal
  happen *before* the authoritative handoff, not after it. The proof
  asserts `credential.disposed` precedes `baton.pass`.
- **`returned-unclean` is a distinct terminal state.** The Job did reach
  review and the result is valid; what did not happen is cleanup, and
  that is not a decoration on success. `bin/v12-poc` now reports
  `credentials_disposed`, `retained_secret` and `unclean_reason`, and
  exits non-zero on it.

`reap()` reports `gone` and `clean` as separate facts, because they gate
different decisions: `gone` gates compensation, `clean` gates calling it
a success. Collapsing them is exactly what let the credential ride out.

A semantic bug of my own surfaced while testing this: "there was nothing
to dispose" was being read as "disposal failed", so a second reap marked
a clean attempt unclean. The fact that matters is that no credential
remains, and that is what is now recorded.

Regressions `R4-1`: the worker-gone/consent-unproven path must report
`returned-unclean` with the secret still present and named; and `reap`
reports absence and cleanliness separately.

### 2 (P1) — compensation `release` had no identity or reconciliation — **fixed**

Confirmed. Round 3 gave `claim` and `pass` effectively-once identities
and reconciliation and left `release` making a single unidentified
attempt — on the path whose entire purpose is reporting whether a claim
is still held. A committed release whose result was lost reported
`stranded` while the Handler was already gone.

`release` now carries a stable per-attempt operation id and goes through
the same `committed()` helper: attempt, replay the identity, then settle
from the public projection (`handler === null` means it committed). The
recap `say` carries an identity too — a committed message whose result
was lost would otherwise be re-sent by a later attempt and duplicate the
recap a human reads.

Regressions `R4-2`: a committed-then-lost release reconciles to
`compensated` after exactly one replay, a genuinely held Handler still
strands, and every manager mutation (`claim`, `pass`, `release`, `say`)
carries an `op-id=`.

### 3 (P2) — the fence omitted the live checkout and alias — **fixed**

Confirmed. `forbiddenPaths()` named the installed binary, the disposable
config and one versioned coordination home, but not `/home/sl/src/baton`
— which the finding explicitly forbids runtime mounts into — nor the
live `/home/sl/baton-v11` alias. The proof caught such a mount only
*after* the worker had run, by inspecting the container. A safety
boundary has to refuse before launch rather than depend on the sample
configuration being honest.

Both are now configured forbidden roots, plus a `forbidden_roots`
configuration hook. Because `assertNoBatonCapability` canonicalizes both
sides, naming them closes direct and symlinked mounts together.

Regression `R4-3` covers the direct mount, a symlink resolving into the
checkout, and an honest adapter tree still passing.

### Two more corrections proposed to W2

Additions to the sixteen above.

19. **Cleanup belongs inside the success boundary, not after it.** A
    contract that says "dispose when the containers are gone" without
    saying "before you report success" permits exactly the path found
    here. v12 should require the terminal report to carry the cleanup
    outcome, and should define a distinct non-success state for work
    that completed without cleaning up.
20. **"Nothing to do" and "failed to do it" are different results.**
    This is the second time in this prototype that collapsing them
    produced a wrong verdict — first for container absence, now for
    credential disposal.

## Response to review 2026-08-21T00:38:29Z (round 5)

### 1 (P1) — an ambiguous recap released completed Work — **fixed**

Confirmed by reading the path, and the review's phrasing is the correct
diagnosis: *carrying an operation id makes a retry possible; it does not
perform one.* Round 4 gave `say` an identity and then called it directly.
A recap that committed and lost its result threw before the `pass`, the
outer catch compensated an **already-complete** assignment, and the Job
went back on the queue — to be executed a second time, with a duplicate
recap to follow. That is worse than the failure it was meant to guard.

`say` now goes through the same `committed()` path as `claim`, `pass`
and `release`: attempt, replay the identity, and only then reconcile.

The reconciliation observation is the **thread**, not the Work. That is
where the answer lives — either the recap is in the discussion or it is
not — and this manager's memory of having sent it decides nothing. So
`committed()` grew an optional `observe` callback rather than always
reading Work detail; the settling question differs per mutation, and
pretending otherwise is what would have forced a wrong predicate here.

The recap stays **before** the pass, deliberately.
`docs/EFFECTIVE-BATON.md` is explicit that handing Work to a human
reviewer without a recap is not acceptable, so moving it after the
handoff would trade one defect for a documented one.

Regressions `R5-1`: a committed-then-lost recap reconciles after exactly
one replay and is not re-sent; a genuinely absent recap still fails; and
a *different* message in the thread does not count as this recap.

### 2 (P2) — successor claims made committed mutations look failed — **fixed**

Confirmed. Both fallbacks asked whether **nobody** holds the Work, which
is a transient observation: the next eligible member may claim between
the mutation committing and the fallback read, and that legitimate
successor then looked like evidence the mutation had not happened —
producing a wrong `stranded` report or the wrong compensation path.

Reconciliation now asks whether **this manager's claim** is gone, which
is the question that was always meant:

- `release` — any Handler other than this participant proves this
  participant's claim is gone;
- `pass` — the ruled destination route plus a Handler that is not this
  participant proves the handoff occurred.

Both carry the observed `successor` in the result, so the fact that
somebody else already picked it up is recorded rather than discarded.

Regressions `R5-2` cover the race in both directions: a successor of
`null`, `poc.rev` and `poc.someone-else` must all reconcile, while Work
still held by *this* participant at the source route must still fail.

### Two more corrections proposed to W2

Additions to the twenty above.

21. **An effectively-once identity is a protocol, not a field.** Minting
    an operation id and never replaying it buys nothing; the contract
    must say attempt, replay, then reconcile. This prototype shipped the
    field-without-the-protocol twice — for `pass` in round 3 and for
    `say` in round 4.
22. **A reconciliation predicate must name the actor, not the absence of
    one.** "Nobody holds it" is transient under concurrency; "my claim is
    gone" is the durable fact. v12 should state each mutation's settling
    observation in terms of the acting participant.
