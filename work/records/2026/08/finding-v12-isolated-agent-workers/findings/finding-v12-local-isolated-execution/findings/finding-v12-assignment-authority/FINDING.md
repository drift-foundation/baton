# Finding: implement the disposable v12 assignment authority

Work `W2928`, child of W1425. This is the first M2 implementation slice.

## Confirmed boundary

Implement a self-contained disposable authority entirely under `v12/` that
owns W151's per-Work assignment contract, monotonic generation, exact live
assignment, fenced generations, typed gates, and operation settlement. It may
reuse or copy v11 concepts but must not import, open, mutate, package or depend
at runtime on `src/baton_work/` or a v11 authority.

The authority, not the Worker Manager, allocates generations and decides
claim, retirement, cancellation, gate and close outcomes. Manager-local or
sidecar identity is non-conforming. V11 compatibility and production migration
are excluded rather than simulated inside this proof.

## Recommended patch ownership

Own new v12 authority/store/transition/projection modules and their tests under
`v12/src/` and `v12/test/`, plus only the self-contained v12 configuration and
disposable-authority setup needed to exercise them. Do not edit Worker Manager,
ACP, OCI/container, conformance-harness, root recipe or v11 product files in
this slice.

## Acceptance

- Shape and return the full `(authority UUID, canonical Work ID, participant,
  positive generation)` assignment identity on v12 claim; never mint a
  generation for a non-v12 contract.
- Centralize every assignment-ending path so Handler/active/live generation
  move atomically and a generation never reappears.
- Implement contract progression, `runtime-quiescence` and
  `contract-runtime` gates, exact-assignment close/cancel, authorized
  unclaimed close, and gate-satisfaction evidence.
- Persist exact operation signatures and replayable results, plus committed,
  refused-when-durable, and retired states/dispositions. Collision and
  ambiguous-settlement races fail closed.
- Prove competing claims, restart before/after claim, settlement timeout versus
  late commit, cancellation and immediate successor races, stale publication,
  operation collision, and generation non-reuse.
- Keep W151's 54/54 executable model green and add implementation tests that
  exercise the real v12 authority through its public boundary.

The implementer revalidates this record, W151 `FINDING.md`/`SPEC.md`, and the
current `v12/` tree before editing. Reviewer proposals do not override the
frozen contract.

## Implementation revalidation — 2026-08-22 (baton.claude, W2928)

W151's `FINDING.md`, `SPEC.md` version `1-ruled`, its 54-scenario evidence
model, and the current `v12/` tree were all re-read before editing. The
contract stands unchanged and nothing here supersedes it. The entries below
are decisions the contract left to the implementation, pinned so review can
rule on them rather than discovering them in a diff.

**Confirmed against the current tree.** The accepted `0-spike` still drives the
DEPLOYED v11 executable as a black-box CLI (`v12/src/baton_cli.mjs`), still
writes `generation: 1`, still carries `W2`-style local selectors in durable
envelopes, and still keeps its issued/spent token map in one manager process.
Those are exactly the three readings §1 supersedes, and they are what the new
authority replaces. The spike is untouched by this slice.

### Pinned implementation decisions

- **This slice implements the AUTHORITY half only.** §3 splits durable facts
  three ways, and the Worker Manager control store — offers, runtime attempts,
  quarantined output, runtime observations, intake and cleanup — is W2929's.
  So `v12/src/authority/` stores none of them. The authority primitives those
  manager transitions are built on ARE here and are proven here:
  `settleOperation` with its `mayRetire` authority, bound disposition and
  collision check is what a settlement timeout uses; the fence is what a late
  runtime meets. An authority that also stored a runtime observation would be
  answering a question §3 says it is not authoritative for.
- **Durable through the built-in `node:sqlite`, not a snapshot of process
  memory and not an npm dependency.** The contract's repeated demand is that
  two facts commit together — fence AND end, contract AND assignment end,
  terminal outcome AND assignment end — so the implementation uses real
  transactions and lets the engine enforce it. A refusal partway through rolls
  back; `test/authority_restart.test.mjs` proves a refused close leaves neither
  a fence, an ending, an event nor an operation record. **Consequence:** the
  v12 subtree's Node floor moves from 20 to **22.5**, recorded in
  `v12/package.json` and the README. `node:sqlite` is still flagged
  experimental by Node and prints one warning; the warning is left visible
  rather than suppressed.
- **The savepoint is the two-kinds-of-refusal mechanism.** §7 distinguishes an
  ordinary refusal, which writes nothing and stays retryable, from one that
  WROTE something durable and is therefore itself a committed outcome. They
  need opposite storage, so the action runs inside a savepoint: an ordinary
  refusal rolls back to it, a durable refusal releases it and records the
  refusal. Integration's stale-target journal is the only transition that uses
  the second form today.
- **A claim's operation signature names the WORK as well as the participant.**
  The evidence model's `claim_signature` is `("claim", participant)` because
  one model `Authority` is one Work. A real authority holds many, and an
  identity meaning "claim by this participant" would collide across them.
  `V12Authority.claimSignature(workId, participant)` is the public form the
  Worker Manager must use.
- **The canonical target is deployment-wide, not per Work.** The model keeps
  `self.target` on each `Authority`, again because one `Authority` is one
  Work. The canonical target is a property of the repository being integrated
  into, so integration compare-and-swaps one deployment-wide value.
- **Route eligibility is enforced on claim.** §7's claim row requires "route
  still permits participant"; the evidence model omits it because it models no
  routes. The authority carries a route per Work and a route/handler table, and
  a claim by a participant the route does not resolve to is refused.
- **Cancellation under `v11` is REFUSED rather than performed.** There is no
  generation to fence, so "fence the exact generation AND end the assignment in
  one transaction" would fence nothing and install a
  `runtime-quiescence:null` gate naming no generation. Half a guarantee spelled
  like a whole one is worse than a refusal; the caller advances the contract
  first. The contract does not say this in as many words — it is derived from
  §5's contract-conditional minting plus §10.5, and it is flagged here for
  review as an implementation ruling rather than a transcription.
- **A plan rejection fences nothing.** Unlike cancellation it invalidates no
  worker capability that was exercised, so it ends the assignment and installs
  `plan-revision:<digest>` without adding a fenced generation. Satisfying that
  gate requires a DIFFERENT plan digest, which is the executable form of §11's
  "cannot reoffer the unchanged plan".
- **`dispose()` releases the store; `close()` terminalizes a Work.** One name
  for both would be an API that invites the wrong one.
- **The fault-injection seam is named and bounded.** §8 turns on the difference
  between "it did not commit" and "I could not ask", so `setLookupAvailable`
  exists to make an unanswerable lookup reachable. It affects `operationResult`
  and nothing else, and the model carries the same seam.

### Acceptance not established here

- The Worker Manager's own effectively-once control store and its
  offer/attempt/quarantine lifecycle. W2929.
- Multi-deployment or v11 migration behaviour. Explicitly excluded: this is a
  disposable authority, it does not migrate, and reopening one under a
  different authority UUID is refused rather than adopted.

## Corrections after independent review — 2026-08-22 (baton.claude)

`review-2026-08-22T06-15-15Z.md` requested changes: four P1s and one P2. All
five are corrected. The reviewer's own reproductions are re-run against the
corrected boundary in `evidence/correction-2026-08-22.txt`.

**The three pinned rulings and the Node floor were reviewed and stand.** The
reviewer found no contract conflict in refusing v11 cancellation, leaving plan
rejection unfenced, or keeping the canonical target deployment-wide. Nothing
below changes them.

### [P1] The public authority no longer exposes its store

The `store` getter is gone. There is no public accessor for the store, the
database, or any SQL runner. The reviewer's reproduction — set
`generation_counter` to 41 through the advertised boundary, then claim and
receive 42 — now fails on an undefined property, and the claim mints 1.

This is checked on the OBJECT rather than in the source, because that is what
a consumer holds: `authority_boundary.test.mjs` walks the instance and its
whole prototype chain for any name matching a store, database or SQL surface,
and refuses any reachable value carrying `run`, `exec`, `prepare` or `close`.
A getter added later is a new door, and the case exists to say there is none.

### [P1] Receipts carry the ruled bindings, their own identities and actors

- **The proposal digest tuple.** `publish` now requires `resultId`,
  `resultDigest`, `candidateDigest`, `inputDigest` and `policyDigest` beside
  the exact assignment and the target, per §10.11 and §4. Each is required,
  each rides the operation signature, and changing any one of them under the
  same proposal id refuses as different bytes.
- **Four typed receipts.** `verification`, `review`, `approval` and
  `integration` are rows in a `receipt` table, each with its own identity, the
  actor who wrote it, and the candidate digest and target revision that actor
  was looking at. Immutability is a unique index on (proposal, kind) rather
  than a check somebody can forget. Approval also records its policy
  generation.
- **Configured capabilities.** A `capability` table backs `verify`, `review`,
  `approve`, `integrate` and `close`; each of those transitions takes an actor
  and refuses one who does not hold it. The hole the review named — publish,
  self-verify, self-review, self-approve, integrate, close — is closed at
  every step, and a regression asserts exactly that sequence refuses.
- **Unclaimed close is authorized.** §7 says an actor holding the configured
  close capability, and `close` had neither an actor nor a check. Both close
  forms now name their actor; holding the assignment is not by itself
  authority to terminalize the Work.

**Pinned:** a deployment MAY grant one participant several capabilities. §10.12
says the receipts stay distinct even then, because each records who wrote it.
What the authority refuses is the question going unasked, not a deployment
answering it that way. A regression covers the permitted case.

### [P1] No-write refusals and settlement authority fail closed

- **Durability moved from the call site to the refusal.** `Refusal` carries a
  `durable` flag set by the transition that RAISES it, and only the
  stale-target integration — which journals its attempt first — sets it. A
  pre-approval integration now writes no attempt row and no operation record,
  and the same operation id still succeeds once the workflow catches up.
- **`mayRetire` defaults to false.** Settlement authority is something a
  caller asserts, never something it inherits by saying nothing. Omitting it
  on an unsubmitted claim returns `live` and retires nothing.

### [P1] Public transitions cannot commit impossible scheduler states

- `createWork` mints an UNCLAIMED Work, so `active` is not reachable; only
  `claim` reaches it.
- `end` derives `queued` with no gate and takes no `phase` or `gate` operand
  at all. A caller supplying one is REFUSED rather than having it ignored: a
  caller whose operand is silently dropped believes it chose the outcome.
- One `#assertPhaseGate` checks the cross-product before any write, for
  creation, every ending path and gate installation: a gate implies `block`,
  `block` implies a gate, and the token must be a typed kind with a non-empty
  detail — an unparseable gate could never be satisfied, because `satisfyGate`
  would have no kind to check evidence against.
- Every one of these refuses with no state and no operation record.
  Invariants remain a backstop rather than post-commit validation.

### [P2] The race proof is deterministic and diagnostic

**Root cause, found rather than guessed:** the racers reported through stdout,
and a pipe's flush races process exit. Four children released by a spin-wait
barrier are exactly the load that loses it, and the parent then parsed an empty
string and threw a JSON syntax error, discarding the exit status, the signal
and stderr.

Each racer now writes its result to a file synchronously, and the harness
reports `spawn-failed`, `no-report`, `malformed-report` and `harness-failure`
as distinct named outcomes carrying the exit status, signal and stderr. It
asserts every racer reached an authority DECISION before it asserts anything
about the decision. Eight consecutive isolated runs are green; a busy timeout
is also now set before the schema rather than inside it, so concurrent opens
wait for the write lock instead of failing to take one.

## Corrections after re-review — 2026-08-22 (baton.claude)

`review-2026-08-22T06-42-24Z.md` confirmed the five original findings as
corrected and raised two remaining P1s. Both are corrected; the reviewer's
reproductions are re-run in `evidence/re-review-correction-2026-08-22.txt`.

### [P1] The runtime boundary is now a different object from the bootstrap

One object carried both the trusted configuration surface and the runtime
consumer surface, and W2929 was directed to consume it. Through the advertised
boundary alone the reviewer claimed as `publisher`, granted `publisher` the
`close` capability, closed the live Work as that actor, and replaced
`canonical_target` — the canonical target moved with zero proposals and zero
receipts. A second reproduction simply passed a configured closer's NAME,
because the check compared a string the same caller supplied.

A capability nobody can take away from you is not a capability, and an actor
identity the caller chooses is not an identity. So:

- **`V12Authority` is the trusted bootstrap.** It certifies contracts, permits
  contract transitions, grants and revokes capabilities, sets policy, creates
  Work, and VENDS sessions. **No transition is on it at all** — there is one
  way to perform one, and it requires a participant binding.
- **`V12Session` is the runtime boundary**, minted by the authority and bound
  to one participant. Every transition lives here and no configuration does.
  The claimant on a claim and the actor on a receipt come from the binding;
  supplying either as an operand is refused rather than ignored, because an
  operand that looks authoritative and is not is worse than none.
- **Sessions are minted, never constructed.** The constructor takes a
  module-local mint symbol exported nowhere, so a consumer reaching the class
  through its own instance's prototype still cannot make one for another
  participant.
- **A session acts only on its own assignments** — with `close` deliberately
  exempt. §7 authorizes close by the close CAPABILITY, and its mandatory
  `expect assignment` is a compare-and-swap operand rather than proof of
  authorship: an approver closing a Work somebody else is executing is the
  ordinary case, and the identity is what stops them closing blindly.

**Pinned, and stated in the module rather than left implied: the trust
boundary is still the filesystem**, exactly as v11 states for its own
authority — whoever can open the store file is the deployment. A session
carries no path, no store and no authority handle, and a deployment does not
hand its manager the store path. What the session guarantees is that holding
it grants no configuration authority and no identity but its own.

### [P1] Approval binds its policy generation

`policyGeneration` was optional and outside the operation signature, so
committing operation `app` under generation 7 and resubmitting the same id
under 8 replayed success — one identity taking two different durable meanings
— and omitting it committed `NULL` while this record claimed approval binds
it. It is now required, validated as a positive integer, carried in the exact
operation signature, and returned on the receipt. §10.13 requires every
durable operand in the operation identity and permits only byte-identical
replay.

## Correction after third review — 2026-08-22 (baton.claude)

`review-2026-08-22T07-12-45Z.md` confirmed the bootstrap/session split and the
approval replay fix, and found one remaining P1 and one P2. Both corrected;
evidence in `evidence/third-review-correction-2026-08-22.txt`.

### [P1] An identity operand is snapshotted, not re-read

The session read `operands.expect.participant` for its binding check and then
handed the **same caller-owned object** to the core, which read it again. A
getter answering `poc.claude` for the first two reads and `poc.gemini`
afterwards passed the check and then ended Gemini's live assignment: the Work
became unclaimed and the event named Gemini.

**Validating one view and executing another is the whole defect**, and no
amount of additional checking fixes it while the object can still change its
answer. The correction is therefore not a better check:

- **`snapshot(value)`** copies an operand into plain frozen data — own
  enumerable properties, each read exactly once, nested values too — and
  refuses a function- or symbol-valued operand outright.
- **The session snapshots the whole operand bag** before it checks anything,
  so there is no second view left to present. Whatever the one read returns is
  the identity for the entire operation: a shape whose single read names the
  session's own participant now refuses on the compare-and-swap, and one that
  names the foreign participant refuses on the binding. Both refuse.
- **`normalizeAssignment`** is that snapshot plus the four-part validation, and
  the CORE applies it to its own `expect` at the top of every transition that
  takes one, with `snapshot` for `satisfyGate`'s evidence.

**Reported honestly: the core layer is defence in depth and is not
independently reachable today.** The session already snapshots and the trusted
face carries no transitions, so removing the core normalization does not fail
the boundary suite. It is kept because a future entry point — or a mistake in
the session wrapper — should not silently reopen the hole, and it is covered
at its own level by a direct test of `snapshot`/`normalizeAssignment` rather
than being claimed as a second proven barrier.

### [P2] `claim` refuses a supplied identity operand

`claim` destructured only `workId` and `operationId`, so a supplied
`participant` was silently dropped and a caller could believe it had been
honoured — contradicting the same correction's rule everywhere else. It now
runs the same strict check: `participant` and `actor` are refused, not
ignored.
