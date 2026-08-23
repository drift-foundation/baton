# Progress: disposable v12 assignment authority

Implementer: `baton.claude`. Work `W2928`, bound to this canonical record.
First M2 implementation slice; W2929 (durable Worker Manager core) depends on
it.

## 2026-08-22 — implementation complete, awaiting review

Read W151's `FINDING.md`, `SPEC.md` version `1-ruled`, its evidence model and
the current `v12/` tree before editing. The contract stands unchanged; what it
left to the implementation is pinned under **Implementation revalidation** in
`FINDING.md`, and the three rulings I derived rather than transcribed are
called out at the end of `PLAN.md`.

### What landed

All new, all under `v12/`:

- `src/authority/schema.mjs` — the durable superset schema of SPEC §5. Work
  state, the per-Work contract selector and generation counter, the live
  assignment, fenced generations, the one typed gate, deployment-wide claim
  slots, assignment/contract events, gate evidence, proposals with their four
  receipts, and the operation journal.
- `src/authority/store.mjs` — the transaction boundary and the effectively-once
  journal. They are one module because they are one mechanism: journalling
  outside the transaction that did the work would let a crash leave a mutation
  with no operation record. A savepoint is what lets an ordinary refusal write
  nothing while a durable refusal keeps what it wrote.
- `src/authority/identity.mjs` — the four-part `assignment_ref`, canonical
  signature serialization (every durable operand including the prose), and the
  typed gate tokens.
- `src/authority/authority.mjs` — the transition table: claim, activity, end,
  pass, cancel, plan rejection, gate arrival, gate satisfaction, contract
  advance, publish, the four workflow receipts, close, `settleOperation`, and
  the invariant assertions of §10.
- `src/authority/projection.mjs` — the read side, with `ready` derived and
  advisory.
- `src/authority/index.mjs` — the public boundary W2929 consumes.

Supporting v12 configuration only: `package.json` (Node floor 20 -> 22.5),
`README.md` (a section on what this is and what it deliberately is not),
`PROVENANCE.md` (the authority is NEW code, not copied v11 material — and the
sentence claiming nothing here opens a SQLite file is qualified rather than
left to contradict the new module), `justfile` (a `test-authority` recipe).

### Tests — 59 new cases

- `test/authority_assignment.test.mjs` (18): the four-part identity; v11 mints
  none; monotonic non-reused generations; deployment-wide capacity; competing
  claim loses atomically; route eligibility; full-identity compare-and-swap on
  four different wrong parts; the immediate same-participant successor; fence
  and end together; the freed claim slot; the quiescence gate and its two kinds
  of evidence; plan rejection; **every one of the seven Handler-clear paths
  through the one ending helper**; phase carries only scheduler meaning.
- `test/authority_operations.test.mjs` (16): exact replay mints nothing;
  differing operands refuse; the prose rides the signature; an ordinary
  refusal writes nothing; a durable refusal replays itself and journals one
  attempt; an unanswerable lookup settles nothing; observe-only settlement; a
  committed claim wins a settlement; a settlement cannot race a commit after
  its lookup; a retired identity stays dead for every submitter; the
  retirement decides the disposition in both directions; collisions fail
  closed; all four operation states.
- `test/authority_contract.test.mjs` (9): contract progression keeps the Work
  and mints on first v12 claim; an uncertified target waits on
  `contract-runtime:` and becomes claimable when certified; stale/unpermitted
  operands refuse; authorized unclaimed close; the close identity rulings
  (omitted, participant-only, stale, fenced, exact); immutable proposal bytes;
  the four ordered immutable receipts; late publication refuses.
- `test/authority_restart.test.mjs` (9): restart before and after the claim;
  fence, gate and contract survive; a retired identity and a durable refusal
  survive; a refused transaction leaves nothing behind; the authority UUID is
  never reassigned; two Works over one store; the history is readable.
- `test/authority_race.test.mjs` (3): **competing claims across REAL
  processes** — four `node` processes synchronized on a wall-clock barrier
  produce exactly one winner and move the counter exactly once; four
  processes replaying ONE fixed claim all get generation 1; and the v11
  cancellation refusal.
- `test/authority_boundary.test.mjs` (4): the self-containment boundary as a
  regression — imports, dynamic imports, code references to the v11 package,
  store, or a spawned process, files created, and the shape of the public
  boundary including the absence of any setter that would let a manager
  allocate its own assignment identity.

### Verification

`v12: npm test` — 137 pass, 0 fail (78 existing plus 59 new). W151's
executable model — 54/54, unchanged. `evidence/verification-2026-08-22.txt`.

Nothing outside `v12/` was touched. The root gate does not call this subtree
and no root test references it, both re-checked.

### One existing gate caught me, and it was right

`v12/test/placement.test.mjs` scans the whole subtree for import specifiers
that are neither Node builtins, nor resolvable inside `v12/`, nor the pinned
ACP dependency. My first multi-process racer built its worker source from a
template containing `from "%MODULE%"`, and the scan refused it. That is the
check doing its job on a specifier that genuinely could not resolve. I changed
the racer to take the module location as an operand instead of teaching the
gate an exception.

### Left deliberately undone

- The Worker Manager control store — offers, runtime attempts, quarantined
  output, runtime observations, intake, cleanup — and its own effectively-once
  journal. That is W2929, and SPEC §3 puts those facts outside the authority.
- Any change to the accepted `0-spike`. It still drives the deployed v11
  executable; replacing that is not this slice's boundary.
- V11 compatibility and production migration, excluded by the assignment.

### State

**Awaiting review.** No review pass has been recorded on this record yet.

## 2026-08-22 — review changes applied, awaiting re-review

`review-2026-08-22T06-15-15Z.md` requested changes with four P1s and one P2.
The review was right on all five, and one of them — the public `store` getter —
made the module's own stated boundary false while a comment asserted it. All
five are corrected; the reviewer's reproductions are re-run against the
corrected boundary in `evidence/correction-2026-08-22.txt`.

### What changed

- **P1a, the store escape.** The `store` getter is gone; there is no public
  route to the store, the database or any SQL runner. The reproduction that
  set `generation_counter` to 41 and then claimed 42 now fails on an undefined
  property and mints 1. `authority_boundary.test.mjs` walks the instance and
  its whole prototype chain rather than the source, because the object is what
  a consumer holds.
- **P1b, the receipts.** `publish` requires the ruled digest tuple —
  `resultId`, `resultDigest`, `candidateDigest`, `inputDigest`,
  `policyDigest` — beside the assignment and target. The four receipts became
  rows with their own identities, their actor, and the candidate digest and
  target revision that actor saw; immutability is a unique index. A
  `capability` table backs verify/review/approve/integrate/close and every one
  of those transitions takes an actor and refuses one who does not hold the
  capability. `close` now names its actor in both forms.
- **P1c, refusals and settlement.** `Refusal` carries `durable`, set by the
  transition that raises it, so only the stale-target integration — which
  journals its attempt — is recorded REFUSED. `mayRetire` defaults to false.
- **P1d, scheduler states.** `createWork` refuses `active`; `end` derives
  `queued` and takes no phase or gate at all; one `#assertPhaseGate` checks
  the cross-product before any write. All refuse with no state and no
  operation record.
- **P2, the race proof.** Racers write their result to a file synchronously
  instead of through a pipe whose flush races process exit — that was the
  actual cause of the empty stdout, found by reproducing rather than guessed.
  The harness names `spawn-failed`, `no-report`, `malformed-report` and
  `harness-failure` as outcomes carrying exit status, signal and stderr, and
  asserts every racer reached a DECISION before asserting anything about it.
  A busy timeout is now set before the schema rather than inside it.

### Tests

Nine new cases (150 total, up from 137), each written to the review's own
words:

- the authority exposes no store, database or SQL runner, and a consumer
  cannot choose the generation;
- the publisher cannot write the receipts that judge its candidate, nor close
  the Work — every step refused, nothing written, identities still retryable;
- a deployment may grant one participant several capabilities, which §10.12
  permits, and the receipts stay separately attributed;
- publication binds every ruled digest and refuses a missing or altered one;
- a refusal that wrote nothing leaves the identity UNSUBMITTED and the same
  operation id succeeds later;
- settlement without explicit authority does not retire;
- a public transition cannot commit an impossible scheduler state; `end`
  derives its outcome and refuses a supplied one; a gate arrival validates its
  token before writing.

### Verification

`cd v12 && npm test` — 150 pass, 0 fail. W151's executable model — 54/54,
unchanged. Eight consecutive isolated runs of the race file, all green.

### Two decisions the corrections introduce

Both are in `FINDING.md` and flagged at the end of `PLAN.md`: where the
capability grant lives (this authority, because the checks are here), and
strict operands on the derived transitions (`end` and `createWork` refuse an
unknown operand rather than ignoring it).

### State

**Awaiting re-review.** W2929 stays blocked until it signs off.

## 2026-08-22 — re-review P1s corrected, awaiting re-review

The re-review confirmed the five original findings as corrected and raised two
more. Both were right, and the first was the same class of mistake as the
store getter it had just closed: I removed the raw SQL door and left the
configuration door beside it, on an object I was directing W2929 to hold.

### What changed

- **The runtime boundary is now a different object.** `V12Authority` is the
  trusted bootstrap — certify, permit, grant, setPolicy, createWork, and
  `session(participant)` — and carries **no transition at all**. `V12Session`
  is minted by it, bound to one participant, and carries every transition and
  no configuration. The claimant and the receipt actor come from the binding;
  supplying either as an operand is refused rather than ignored. Sessions are
  minted through a module-local symbol, so a holder cannot construct one for
  somebody else.
  A session acts only on its own assignments, with `close` exempt: §7
  authorizes close by the capability, and its mandatory `expect assignment` is
  a compare-and-swap operand, not proof of authorship.
- **`policyGeneration` is required**, validated, in the operation signature,
  and returned on the receipt.

### Tests — 3 new cases (153 total)

- the runtime face carries the transitions and none of the configuration, and
  exposes no route back to the authority or the store;
- a session holder cannot self-grant, impersonate a configured actor, move the
  canonical target, or mint a session — the reviewer's two reproductions;
- the trusted face configures and vends and carries no transition;
- an approval binds its policy generation: missing and six mistyped forms
  refuse before writing, the committed one records and returns 7, the same
  operation id under 8 collides, the byte-identical replay returns, and the
  journal signature carries it.

The whole existing suite moved onto sessions, which is also how the production
consumer will read.

### What I could not close, and said so instead

The trust boundary is still the filesystem: anybody who can open the store
file is the deployment. A session carries no path, no store and no authority
handle, but a manager that independently knows the path can open its own
authority. That is exactly v11's stated model for its own authority, and it is
now written into the module and the finding rather than implied by omission.

### Verification

`cd v12 && npm test` — 153 pass, 0 fail. W151's model — 54/54. Six isolated
race runs green, so the corrected P2 survived the refactor.
`evidence/re-review-correction-2026-08-22.txt`.

### State

**Awaiting re-review.** W2929 stays blocked, and consumes `V12Session`.

## 2026-08-22 — third-review P1/P2 corrected, awaiting re-review

The review confirmed the split and the approval fix and found a TOCTOU I had
walked straight past: the session validated `expect.participant` and then
handed the caller's own object to the core, which read it again. A getter that
changed its answer after two reads ended another participant's live
assignment.

### What changed

- **`snapshot(value)`** — one read of each own enumerable property into plain
  frozen data, nested values included; a function- or symbol-valued operand is
  refused. The session snapshots the whole operand bag BEFORE checking
  anything, so there is no second view to present.
- **`normalizeAssignment`** — that snapshot plus the four-part validation,
  applied by the core to its own `expect` on every transition that takes one,
  and `snapshot` for `satisfyGate`'s evidence.
- **`claim`** runs the same strict-operand check as every other session entry
  point, so `participant`/`actor` are refused rather than dropped.

### Tests — 4 new cases (159 total)

- a getter and a Proxy identity cannot cross the boundary, and the foreign
  Work, its assignment, its events, its activities and the operation journal
  are all unchanged;
- all eight assignment-owned transitions take the same snapshot;
- `claim` refuses `participant` and `actor`;
- the snapshot primitive itself: each property read exactly once, stable
  afterwards, frozen, nested, and refusing callable operands.

### What the mutation check actually showed, and what I am NOT claiming

Removing the session snapshot fails both TOCTOU regressions. Removing the
CORE normalization fails nothing — the session already snapshots and the
trusted face carries no transitions, so that layer is not independently
reachable today. I kept it, because a future entry point or a slip in the
session wrapper should not silently reopen the hole, but it is reported as
defence in depth rather than a second proven barrier, and it is covered at its
own level by the direct `snapshot`/`normalizeAssignment` test instead.

### Verification

`cd v12 && npm test` — 159 pass, 0 fail. W151's model — 54/54. Six isolated
race runs green. `evidence/third-review-correction-2026-08-22.txt`.

### State

**Awaiting re-review.** W2929 stays blocked and consumes `V12Session`; the
reviewer's condition that it receive only its session — not the store path or
the trusted bootstrap — is recorded in `PLAN.md` step 9.
