# Progress

Implementer: `baton.claude`. Canonical Baton Work: W2929.

**State: awaiting review of the FIRST SLICE. This Work is not finished.**
Plan item 2's foundation — the contract boundary and the durable control
store — is landed and verified. Plan items 3 and 4 are **not started**: no
offer/claim orchestration, no attempt lifecycle, no agent-session
normalization, no adapter interface. The Work is passed back rather than held
so the foundation can be reviewed before orchestration is built on it, and
`next` is set to `baton.impl` so it returns here for the next slice.

Saying that plainly matters more than the size of the slice: the acceptance
boundary is long, and a reader who sees two green suites should not have to
infer which parts of it are still absent.

## What landed

### `v12/src/worker_manager/contracts.mjs`

Everything below orchestration that decides whether a document may be
trusted: exact §2 negotiation, §3.2 canonical bytes and digests, the §4.2
operation signature, the claim-token verifier, and the §12 rules a schema
cannot express. It reaches no database, adapter or provider.

**Both W4487 integrity boundaries are implemented as the plan's item 1b
pins them, not re-derived.**

- The operation-signature payload is the canonical digest of
  `{"kind", "operands"}`, with a bearer operand entering as its VERIFIER and
  `null` staying `null`. A receiver recomputes it for a COMMAND and refuses
  `integrity.digest` before the operation is journalled; a reply is exempt,
  keyed on `message_type`, and the same document sent as a command is
  refused so the exemption cannot become a hole.
- The verifier is W151 §7's one derivation — `"sha256:" + hex(SHA-256(bearer
  UTF-8 bytes))`. The golden pair is pinned as a LITERAL and cross-checked
  against the design model's own literal, so this third copy cannot drift
  from the two the conformance package already compares.

The schema is a SEALED byte copy of the frozen asset with a regression
asserting byte identity. The closed error PAIRING is written out here,
because the frozen schema carries the two vocabularies flat and does not pair
them — with a regression asserting the union of the pairs is exactly the
schema's enums, so a code added to the contract fails loudly rather than
becoming unmappable.

### `v12/src/worker_manager/schema.mjs` and `store.mjs`

One SQLite control store under the external state root, with an explicit
path and no ambient default. `transact` is the atomic boundary and `replay`
is what makes a repeated request return the first outcome; they are one
mechanism, and the action runs inside a savepoint so an ordinary refusal
vanishes while a durable one survives with its writes.

The table set is the argument: offers, attempts, the MANAGER's own operation
journal, observations and profiles — and no Work state, no generation
counter, no claim. A manager that stored those would be a second authority.
A regression asserts both halves: the manager's tables exist and the
authority's do not.

`offers_one_live_per_work` is a partial unique index over the two
nonterminal states, so two manager PROCESSES racing on separate connections
cannot both hold a live offer. A read-then-write check could not give that;
both would pass it.

### Regressions — 25 new cases

`test/worker_manager_contracts.test.mjs` (17): schema byte identity, the
error-pairing agreement, canonicalization and its §3.2 refusals, the golden
verifier against a literal and against the model's, the signature covering
the kind, the bearer riding as its verifier, the stale-signature refusal
(the W4487 reviewer's exact reproduction, on the product path), the reply
exemption and its command counter-case, exact negotiation, the durable-secret
walk at depth, the `offer.decide` binding, acceptance still proving
possession, the error pairing, the Work-id prefix, and the frozen decline
vector validating unchanged through the product validator.

`test/worker_manager_store.test.mjs` (8): explicit path and own schema,
restart by reopening the file, exact retry replaying byte-for-byte while
performing nothing, operation collision changing nothing, ordinary refusal
staying retryable, durable refusal surviving and replaying, one-live-offer
across two processes with terminal states freeing the Work and other Work
unaffected, and a sweep of every column of every table proving no bearer
reaches the file while the verifier does.

## Verification

- `cd v12 && TMPDIR=<bracket> npm test` — **186 pass, 0 fail** (161 before);
  the bracket retained zero test-owned roots.
- W151 model 64, worker-control model 24, conformance 74, ACP boundary 56 —
  all passing, so the 144 relevant design tests and the separately counted
  conformance package are green.
- Whitespace-damage check clean.

The new fixture family `v12-manager-` is registered in the W2907 shared
owned-root registry's family list, so the cleanup regressions account for it.

## Not started — plan items 3 and 4

- offer issue/decision/expiry/restart and fixed claim settlement against an
  injected `V12Session`;
- assignment activation, orthogonal attempt observations, cancellation
  ordering, output freeze/intake, cleanup;
- provider-neutral agent-session profile certification, session/turn/event
  normalization, durable event observation;
- the runtime and agent adapter interfaces and their scripted doubles.

The store's tables for offers, attempts and observations exist and are
exercised directly by the regressions above; nothing orchestrates them yet.

## Review notes

Two choices worth a second opinion, both in `FINDING.md` under
"Implementation revalidation — 2026-08-22":

1. The Draft 2020-12 validator is **not yet chosen** — the non-blocking open
   decision. This slice validates the semantic rules and the seals by hand
   and does not yet run documents through a schema validator, so
   "unknown-field refusal" from the acceptance list is not covered. That is
   a gap, named rather than glossed.
2. The closed error pairing is written out in product code because the frozen
   schema does not express it. The agreement regression is what keeps it
   honest, but a reviewer may prefer the pairing move into the contract
   asset instead.

## Round 2 — the five P1s and the P2 (2026-08-22)

`review-2026-08-22T16-37-37Z.md`. All six reproduced against the tree before
any edit; all corrected. Evidence:
`evidence/correction-first-slice-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. This round corrected the
foundation the review named; it did not build on it.

### What I had wrong

The largest is the first: I shipped a "trust entry" that never ran the frozen
schema, and exempted from signature checking every `message_type` that was not
the exact string `command`. One misspelled discriminator turned a mutating
command with a stale operation signature into the reply exemption — reopening
the W4487 hole that two review rounds had just closed at the contract level.
I had described the exemption as safe BECAUSE it was keyed on `message_type`,
without anything establishing that field.

`ajv` 8.20.0 is now pinned exactly and the schema runs before any semantic
helper; `verifyOperationSignature` refuses outright unless the caller passes
the schema-proven flag, so the exemption cannot be reached by skipping the
schema.

### The other five

- **Negotiation** now takes the manager's own extension support, limits and
  certified profile, selects the exact intersection, and returns the complete
  frozen welcome body — validated as one before it is handed back, because a
  manager that cannot form a valid welcome has a fault of its own. Limits
  intersect at the minimum: each bound says what its side can survive.
- **Observations** are keyed by their full source scope
  `(attempt, incarnation, source_seq)`. The contract scopes `source_seq` to
  one incarnation and my key did not, so an adapter restart was
  indistinguishable from a conflicting duplicate before any monotonic logic
  ran. `manager_seq` is separately unique per attempt.
- **Durable refusals** store the whole sealed outcome, so a `policy.retention`
  replays as itself rather than as a fabricated `refused.precondition`. The
  regression now uses a pair other than that one — as the review points out,
  my original case chose the fabricated pair and hid the loss.
- **The store** inspects before it mutates, initializes a fresh store in one
  transaction, sets the busy policy before taking a lock, and closes the
  handle on every constructor failure. The regression asserts the file BYTES
  are unchanged after a refused open, not just the table list.
- **Canonicalization** refuses negative integers, negative zero, lone
  surrogates, sparse arrays and non-plain objects.

### One existing case strengthened, deliberately

`placement.test.mjs`'s v11-isolation guard hardcoded one permitted package. It
now reads the allowed set from `package.json` and requires each declared
version to be an exact pin — so it still fails for an undeclared import and
now also fails for a declared-but-floating one. Widening a guard to admit a
new dependency is a decision, and it is recorded rather than made silently.

### Verification

- `cd v12 && TMPDIR=<bracket> npm test` — **193 pass, 0 fail** (186 before);
  the bracket retained zero test-owned roots.
- W151 64, worker-control 24, conformance 74, ACP boundary 56.

### State

**Awaiting re-review of the corrected foundation.**

## Round 3 — the corrected foundation's own five (2026-08-22)

`review-2026-08-22T17-30-46Z.md`. All five reproduced before any edit; all
correct. Evidence: `evidence/correction-foundation-round2-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Two rounds have now corrected the
foundation; neither built on it.

### What I had wrong

The first is the same bypass a third time, and I introduced it while fixing
the second: my round-2 correction gated the reply exemption on a boolean the
CALLER passed. Nothing bound `{schemaProven: true}` to AJV having validated
that document, so the exported helper accepted a misspelled discriminator
with a stale signature — the W4487 hole again, through a door I built while
closing the previous one. A proof a caller can write is not a proof. The
helper is private now and the exemption follows from a brand only the
validator applies.

The other four: the trust entry returned its input rather than an owned copy,
so "validated" was a time-of-check/time-of-use alias; `replay` used `null` for
both absence and a committed null, so an exact retry ran the action again;
the surrogate check ran on values but not member names; and the manager's own
negotiation policy was trusted while the peer's hello was proven.

### Two mutation results I am recording rather than hiding

**Mutating one of the two presence checks left the suite green** — the other
caught the retry. The faithful mutation is both at once, which is what the
original code was, and that fails the two null-result cases.

**The brand check is NOT witnessed and cannot be from outside the module.**
`verifyOperationSignature` is private and its only caller validates first, so
the guard is unreachable by construction. What the suite witnesses is the
property the review asked for: the export is gone and the forged frame is
refused. The brand stays as defence for the orchestration callers this slice
does not yet have, recorded as unwitnessed rather than presented as covered.

### One test fixture corrected

`declineBody()` shared the module-level `WORK_REF` object, so the new
ownership case's deliberate mutation corrupted every later case. It deep-copies
now — and the failure was loud, which is the only reason I caught it.

### Verification

- `cd v12 && TMPDIR=<bracket> npm test` — **200 pass, 0 fail** (193 before);
  the bracket retained zero test-owned roots.

### State

**Awaiting re-review of the corrected foundation.**

## Round 4 — the foundation's third round (2026-08-22)

`review-2026-08-22T18-14-12Z.md`, two P1 and one P2. All three reproduced
before any edit; all correct. Evidence:
`evidence/correction-foundation-round3-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Three rounds have now corrected
this foundation and none of them built on it. The review says so and is right
to keep saying so.

### What I had wrong

**The promised manifest trust entry did not exist.** The module header
claimed exact schema AND semantic validation below orchestration, and the
validator setup justified leaving `format: "uri"` assertions off by naming a
`validateUri` that "enforces below" — a helper nothing had written. The
comment argued for disabling the weaker check on the strength of a stronger
one that was not there. A copy of the frozen valid manifest carrying
`https://source.invalid/archive?token=secret` passed everything this module
offered.

**The journal could durably store the bearer.** `assertNoDurableSecret`
walked correctly and `transact` never called it. The existing file-wide sweep
proved a property of its own fixture, not of the boundary.

**A database without Baton metadata was adopted as fresh.** Absence of
Baton's metadata is not evidence that a file belongs to Baton — it is equally
the signature of somebody else's store.

### Changed

`validateManifest` is the copied, schema-first trust entry, with the pure §12
rules: work-id prefix, names unique across sources and outputs, destinations
pairwise NON-OVERLAPPING rather than merely unequal, credential-free locators
read off the ORIGINAL text rather than a parser's reconstruction, manifest
digests over the document with the member OMITTED, content-manifest sorting
and uniqueness in one pass with recomputed aggregates and tree seal, git
object-format consistency, and the durable-secret walk. Artifact references
and content manifests are found by a WALK, not a field list — the human
contract's locator sits in a member no §12 rule names and is exactly as
durable as a source's.

Rules 2 and 11 are deliberately absent and named: both need orchestration
state this slice has none of.

The journal refuses a committed result or a sealed refusal carrying a secret,
inside the transaction — a committed mutation whose journal row was rejected
is the effectively-once mechanism's worst state. The store initializes only a
genuinely empty schema and refuses an existing unowned database with the
bytes unchanged.

### One of my own tests passed for the wrong reason, and a mutation found it

The frozen record expresses an invalid vector as a PATCH against a named
valid one. My first version applied the patch and did not reseal
`manifest_digest`, so both semantic vectors were refused by the digest check
and never reached the rule they exist to witness — removing the entire
input-manifest semantic block left them green. `patched()` reseals now, and
the assertion requires the refusal the record NAMES rather than any
ContractError.

Recorded rather than quietly repaired: a vacuous vector test is worse than no
vector test, because it reads as agreement with the frozen contract. Two more
fixtures of mine were wrong about which layer refuses them; both now assert
the schema ACCEPTS the document first, so each case witnesses §12 and not the
schema.

### Verification

- `cd v12 && npm test` — **213 pass, 0 fail** (202 before); under a TMPDIR
  bracket, zero test-owned roots retained.
- All four design models green: assignment state machine 64, ACP boundary 56,
  runtime conformance 74, worker-control API and manifests 24. The last is
  the one that matters here — it validates the same frozen vectors from the
  design side, so the product entry and the model now agree about manifest
  documents and not only about envelopes.
- Five mutations, each independent; each fails exactly the cases that name it.
- Whitespace check clean.

### State

**Awaiting re-review of the corrected foundation.**

## Round 5 — the foundation's fourth round (2026-08-22)

`review-2026-08-22T18-51-48Z.md`, three P1. All reproduced before any edit;
all correct. Evidence:
`evidence/correction-foundation-round4-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Four rounds have now corrected
this foundation and none of them built on it.

### What I had wrong

All three are in code I landed LAST round, which is worth saying plainly: the
manifest trust entry closed a real hole and opened three smaller ones.

**A parse failure was ignored.** `validateUri` caught every `new URL` error
under a comment asserting that a failure meant an opaque scheme. `https://[`
is not opaque — it is malformed — and this module's own header argues for
turning AJV format assertions off, so nothing else was going to catch it.

**Content entries sorted by UTF-16 code units.** JavaScript `<` is not the
bytewise order §3.3 names. `"\u{10000}.txt"` sorts below `"\uE000.txt"` under
`<` and above it under UTF-8 comparison, so the product accepted a list the
contract calls unsorted — and the frozen model implements the other order.
Two conforming readers disagreeing about canonical tree order is the exact
failure a seal exists to prevent.

**The secret walk screened field NAMES.** A raw bearer under `diagnostic`
committed, and one interpolated into a durable refusal message was journalled
and replayed. A name-only check reads as a leak boundary while being a naming
convention.

### Changed

A parse failure refuses, with every valid form measured rather than assumed
to survive it. `_bytewise` compares UTF-8 bytes. The walk examines values as
well as names and refuses any string CONTAINING a known bearer — containment
rather than equality, because an interpolated message carries the secret as
durably as a bare field does.

Shape is explicitly not a substitute: the contract admits bearers from 32 to
4096 characters, so a rule refusing token-shaped strings would refuse
ordinary durable operands and still miss a short one. The manager therefore
holds the values it knows, with `rememberSecret`/`forgetSecret`/`withSecret`
for the orchestration slice — `withSecret` releases in a `finally`, since a
throwing caller must not leave a value live. The golden vector is seeded
because it is the one bearer this build holds as a constant. The VERIFIER is
deliberately not refused; a check that refused it would make the durable
offer record impossible, and a regression says so.

### Verification

- `cd v12 && npm test` — **222 pass, 0 fail** (217 before); zero test-owned
  roots retained under a TMPDIR bracket.
- All four design models green: 64, 56, 74, 24.
- Five mutations, each independent. M4 — containment weakened to equality —
  fails only the interpolated cases, which is precisely why they exist.
- `pytest -n auto -m "not serial" tests/work` — 2925 passed, 3 failed;
  codex-event-bridge 297/297; acp-baton-bridge 55/55; whitespace clean.

### The three pytest failures are not this Work's

W4996 reviewer cases from `review-2026-08-22T19-04-09Z.md`, which landed
while this turn was running. W4996 is queued on `baton.impl` for its own turn
and shares no module with `v12/src/worker_manager/`.

### State

**Awaiting re-review of the corrected foundation.**

## Round 6 — the foundation's fifth round (2026-08-22)

`review-2026-08-22T19-11-31Z.md`, two P1. Both reproduced before any edit;
both correct. Evidence:
`evidence/correction-foundation-round5-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Five rounds have now corrected
this foundation and none of them built on it.

### What I had wrong

Both are in the secret boundary I landed LAST round. The value-aware check
closed the reported leak and left two adjacent ones.

**The journal validated a different object from the durable JSON.** The walk
read the action's result and `JSON.stringify` read it again for the row — two
observable reads of a value the manager did not construct. A `toJSON` returns
the bearer while `Object.entries` shows only the method, so the guard passed
and the raw bearer committed.

**Secret scopes released values that were still live.** A `Set` records
presence, not ownership, so an inner `withSecret` on a value an outer owner
already held deleted the outer's entry — including, for the seeded golden
bearer, the seed itself. And `withSecret` released as soon as the act
RETURNED, which for a provider act means at Promise creation: unregistered
while the work was still pending, in exactly the call shape the orchestration
slice will use.

### Changed

`_durable` serializes once, walks the parse of those exact bytes, and records
the same bytes. It does not reserialize after validating, which would reopen
the identical gap for a stateful `toJSON`.

Two registers replace the Set, because two lifetimes were conflated: the
build's own golden bearer is PINNED and never released — nothing acquired it,
so nothing may hand it back — and live values are REFERENCE COUNTED, so a
value stays live until its last owner releases it and an unbalanced release
is inert rather than going negative. `withSecret` transfers ownership to the
continuation when the act returns a thenable, releasing on settle; a
synchronous throw still releases immediately.

### One alternative considered and not taken

The review offers removing the scoped API until its real orchestration caller
can define the lifetime. I kept it: it is what makes the boundary usable
rather than a convention to remember, and both of its failure modes are
regressions now rather than possibilities. Deleting it is a small change if
the reviewer would still rather it wait, and that is said on the thread.

### Verification

- `cd v12 && npm test` — **229 pass, 0 fail** (225 before); zero test-owned
  roots retained under a TMPDIR bracket.
- All four design models green: 64, 56, 74, 24.
- Six mutations, each independent. M1 breaks the ORDER and only the
  reviewer's case sees it; M6 keeps the order and adds a second
  serialization, which only a read COUNT can see — two halves of one rule,
  each needing its own case.
- `pytest -n auto -m "not serial" tests/work` — 2931 passed, 1 failed;
  codex-event-bridge 297/297; acp-baton-bridge 55/55; whitespace clean.

### The one pytest failure is not this Work's

`test_w4996_review_a_walk_memo_cannot_hide_a_cycle_on_another_path`, from a
W4996 review that landed while this turn was running. It is a real concern
against the depth memo I added to W4996 earlier today; that Work is queued on
`baton.impl` for its own turn and shares no module with
`v12/src/worker_manager/`.

### A note on the review's own verification

It records that the complete v12 gate could not run under the managed review
policy — unrelated fixture and placement cases need nested process spawns and
receive EPERM — and that no escalation was requested. The full gate does run
here and is green at 229, including the reviewer's three cases and the four
added this round.

### State

**Awaiting re-review of the corrected foundation.**

## Round 7 — the foundation's sixth round (2026-08-22)

`review-2026-08-22T19-31-47Z.md`, two P1. Both reproduced before any edit;
both correct. Evidence:
`evidence/correction-foundation-round6-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Six rounds have now corrected this
foundation and none of them built on it.

**Closed by this review:** the scoped secret API stays. I offered to remove
it last round; the review says reference counting and ordinary Promise
behaviour are sound and that one-read thenable adoption closes its remaining
boundary.

### What I had wrong

Both are last round's corrections, split one level down — the same mistake
twice, at a smaller scale.

**The first committed result was not the durable result.** Round 5 recorded
the exact serialized bytes and left `transact` returning the caller's object,
so a `toJSON` gave the first caller the mutable source and an exact retry the
parsed journal: two answers under one operation identity for an act that ran
once.

**Thenable classification consumed a different continuation than settle.**
Reading `outcome.then` to decide, then handing `outcome` to
`Promise.resolve`, is two reads of an attacker-controlled getter — exactly
the shape of the serialization finding I had just fixed. A stateful thenable
offering its continuation once was classified asynchronous while the
continuation was never called, so the wrapper settled and released the bearer
with the act still pending.

The lesson is one sentence and it applies to both: A READ THAT DECIDES
SOMETHING MUST BE THE READ THAT IS USED.

### Changed

`_durable` returns `{bytes, committed}` from the one serialization;
`committed` is the parse of exactly those bytes and is what every caller
gets. `withSecret` captures the continuation once and assimilates that
callable with its original receiver; a throwing getter still lands in the
synchronous cleanup, which now has its own regression.

### One mutation result recorded rather than papered over

Returning `JSON.parse(durable.bytes)` per caller instead of the one parsed
copy leaves the suite green — and that is CORRECT rather than a hole. Each
call would produce its own unowned copy of the same bytes, so canonical,
byte-stable and nobody's-alias all still hold. It is an equivalent
implementation with one extra parse, not a defect the suite missed, and
adding a test to pin my arbitrary choice would be worse than saying so.

### Verification

- `cd v12 && npm test` — **236 pass, 0 fail** (231 before); zero test-owned
  roots retained under a TMPDIR bracket.
- All four design models green: 64, 56, 74, 24.
- Five mutations, each fails the cases that name it.
- `pytest -n auto -m "not serial" tests/work` — 2938 passed, 1 failed;
  codex-event-bridge 297/297; acp-baton-bridge 55/55; whitespace clean.

### The one pytest failure is not this Work's

`test_w4996_review_a_cycle_cut_by_the_cap_is_not_invented`, from a W4996
review that landed while this turn was running, against the cycle boundary I
added there earlier today. W4996 is queued on `baton.impl` for its own turn.

### State

**Awaiting re-review of the corrected foundation.**

## Round 8 — the release answer (2026-08-22)

`review-2026-08-22T19-49-19Z.md`, one P2. Reproduced before any edit;
correct. Evidence:
`evidence/correction-foundation-round7-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Seven rounds have now corrected
this foundation and none of them built on it.

### What I had wrong

`forgetSecret` documents its boolean as whether the value is now gone, and my
own comment said a pinned value never is. It then deleted the last dynamic
registration and returned `true` without consulting `_PINNED`.

Not a leak — the guard is the boundary and it kept refusing the value
correctly — but the exported answer said the opposite of the state the guard
enforces. Orchestration reading `true` and concluding the value is no longer
live would be reasoning from a false report, which is the kind of defect that
stays invisible until something depends on it.

### Changed

`return !_PINNED.has(value)`. The nested count, the inert unbalanced release
and the permanent pinned protection are untouched.

### The added case asserts agreement, not a return value

A boolean has two ways to be wrong, and the reported case pins only one:
always answering "still live" would satisfy it while breaking every ordinary
release. So the new case probes the GUARD after every release and requires
the two to agree — through nested owners on an ordinary value, after balanced
and unbalanced releases of a pinned one, and through the scoped form. The
boolean is only meaningful as a description of the guard, so that is what is
asserted.

### Verification

- `cd v12 && npm test` — **238 pass, 0 fail** (237 before); zero test-owned
  roots retained under a TMPDIR bracket.
- All four design models green: 64, 56, 74, 24.
- Two mutations, each fails the cases that name it.
- `pytest -n auto -m "not serial" tests/work` — **2942 passed, 0 failed**;
  codex-event-bridge 297/297; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green**, with no failure belonging to another
Work — the first time that has been true in this sequence.

### State

**Awaiting re-review of the corrected foundation.**

## Round 9 — the inert branch (2026-08-22)

`review-2026-08-22T20-00-37Z.md`, one P2. Reproduced before any edit;
correct. Evidence:
`evidence/correction-foundation-round8-2026-08-22.txt`.

**Still not started:** plan items 3 and 4. Eight rounds have now corrected
this foundation and none of them built on it.

### What I had wrong

The same contradiction as last round, in the branch I did not fix. Round
eight pinned the boolean as a description of the guard's CURRENT liveness and
corrected the last-owner branch; the `held === undefined` branch still
returned `false` unconditionally. So releasing an ordinary value twice
reported "still live" while the guard correctly permitted it, because it was
gone.

The call is state-inert — nothing to decrement, nothing to delete — but the
answer is not a report of what the call did. Both branches consult the same
fact now.

### Two things worth recording, and both are mine

My round-eight agreement case asserted the rule in both directions and
stopped at the last owner, so the branch that answers when there is no owner
was never asked. An agreement case that does not visit every branch is
agreement about the branches it happened to visit.

Worse, an EARLIER case of mine asserted the wrong answer outright — the
registrations-nest case required `false` after the last release, which is
exactly the contradiction the next case pins. It asserted the defect. A test
that pins the wrong answer is worse than a missing test, because it argues
against the correction.

### Verification

- `cd v12 && npm test` — **239 pass, 0 fail**; zero test-owned roots
  retained under a TMPDIR bracket.
- All four design models green: 64, 56, 74, 24.
- Three mutations, one per branch of a three-line function — the boolean has
  three ways to be wrong and the reported case pins one.
- `pytest -n auto -m "not serial" tests/work` — 2953 passed, 3 failed;
  codex-event-bridge 309/311; acp-baton-bridge 55/55; whitespace clean.

### The five failures are not this Work's

Three are W4996 reviewer cases and two are W2845 reviewer cases against the
matrix oracle I landed there earlier this session — both reviews landed while
this turn was running.

### State

**Awaiting re-review of the corrected foundation.**

## Plan item 3, first half — the offer and the claim (2026-08-22)

`review-2026-08-22T21-05-52Z.md` **signed off foundation item 2** and said to
implement items 3 and 4. This turn implements the OFFER AND CLAIM half of
item 3 — the dossier's own steps 1 through 6 plus the restart rules. Evidence:
`evidence/offer-claim-slice-2026-08-22.txt`.

The foundation was revalidated before anything was built on it: 239 v12 cases
green against the tree as it stood.

### Not implemented, and said plainly

- The rest of item 3: assignment activation, runtime start and reconciliation
  by opaque runtime id, the ten orthogonal observation axes, cancellation
  ordering, output freeze, intake and cleanup.
- All of item 4: the provider-neutral agent-session profile, session/turn/
  event normalization, and the runtime/agent adapter contracts.

### What landed

Every step is a durable fact rather than an inference, because the question
this boundary answers is whether the next incarnation can tell what happened.

Reads before entropy — a bearer minted for an offer that is then refused is a
secret that existed for no reason. The per-Work CAS is the database's, since
two processes both pass a check made outside the write. Acceptance consumes
the verifier, freezes the intent, derives the fixed operation id and stores a
separate settlement deadline; a decline consumes the verifier too, so it can
never be replayed into an acceptance.

A lost result may only be OBSERVED before the deadline: a read saying "not
committed" proves only its own instant, and retiring early could close an
identity the authority is still going to honour — the manager would record a
refusal for a claim that won. Positive refusal evidence retires immediately,
because that is an answer rather than a guess, and every path adopts a bound
retirement rather than re-deciding it.

Restart is asymmetric on purpose. A prior incarnation's ISSUED offer is
abandoned but stays visible with its verifier consumed; an ACCEPTED one is
recoverable because acceptance froze its authorization; and this
incarnation's own issued offers are untouched, since several managers
coordinate through one store.

### One signed-off line changed, and it is recorded

`validateOfferDecide` compared the verifier with `!==`, which exits at the
first differing byte — on the one comparison that decides whether authority
is taken. It uses `timingSafeEqual` now. I wrote a second constant-time
comparison in `offers.mjs` first and then removed it: two comparisons where
one exits early leaves the leak where it was, so the fix belongs in the
module that owns the derivation.

### Two defects of my own, both found by measuring

**M6 passed green because the case it named was a tautology.** It asserted
`row.claim_operation_id === claimOperationId(...)` — both sides call the same
function, so any implementation satisfies it. The property a minted id cannot
satisfy is the one the derivation exists for: a LATER incarnation, holding
only the durable row, names the exact operation the first submitted. That is
what the case does now.

**The first version of this suite leaked twenty temporary roots**, caught by
running the gate under a `TMPDIR` bracket rather than by reading the code. It
uses the W2907 shared owned-root registry now.

### Verification

- `cd v12 && npm test` — **256 pass, 0 fail** (239 before); zero test-owned
  roots retained under a bracket.
- All four design models green: 64, 56, 74, 24.
- Six mutations, each fails the cases that name it.
- `pytest -n auto -m "not serial" tests/work` — 2960 passed, 1 failed (a
  W4996 reviewer case that landed mid-turn); codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting review of the offer and claim slice**, with the rest of item 3 and
all of item 4 still to come.

## Item 3a corrected — 2026-08-22

`review-2026-08-22T21-36-26Z.md`, six P1. All reproduced before any edit; all
correct. Evidence: `evidence/correction-offer-claim-2026-08-22.txt`.

### What I had wrong

Two of the six were invisible to my own suite for one reason: **a scripted
double can agree with an implementation about a shape neither shares with the
authority.** The settlement signature was stored as NULL and passed as
`undefined` — an operation collision against a real committed claim, and a
value the authority's NOT NULL column cannot hold. And `V12Session.claim`
returns the assignment DIRECTLY while both recording paths read
`result.assignment`, so the authority held a live generation while the manager
durably recorded `assignment: null`. A record that disagrees with the
authority is worse than none, because a restart trusts it.

The other four: the participant was an operand nothing compared with the
session's binding; expiry threw without settling, leaving an unspent verifier
holding the per-Work slot forever; the terminal transition updated `accepted`
rows too, so a stale decline could destroy the authorization acceptance had
just frozen; and certification was conditional on the argument being supplied
— which my happy-path fixtures never supplied, which is how it survived.

### Changed

The acceptance freezes `V12Authority.claimSignature(...)`, imported rather
than restated because a third copy of a signature rule is a third thing that
can drift. Both paths record the assignment the authority returned. The
binding decides the participant. Expiry CASes to `expired`, consumes the
verifier and releases the slot. Issued-only transitions CAS from `issued`
alone. Certification prefers the control store's `profiles` row, accepts an
explicit assertion that does not contradict it, and refuses absence.

The issue signature covers every durable operand, and an exact re-issue
REFUSES: the bearer existed only in the process that minted it, so a second
call cannot reproduce one and must not hand back a secret that does not
derive the stored verifier.

### Two mutation results recorded

**The issued-only CAS is unwitnessed and I could not witness it.** Acceptance
spends the verifier, and the verifier check refuses before the CAS is
reached; restart filters accepted rows first. No reachable path drives it
today. It stays as defence for the callers the rest of item 3 will add, and
the race cases assert the OUTCOME rather than which guard fired.

**The replay guard was green against the reviewer's retained case**, which
permits either a throw or a matching pair and so cannot tell "refused" from
"replayed something usable". My case pins the answer — and had to pin the
runtime attempt id too, since it is a durable operand defaulting to a fresh
UUID.

### Two fixture corrections of my own

The scripted double now carries a `participant` and returns the assignment
directly, exactly as `V12Session` does — a wrapper there was half of why the
shape mismatch survived. And certification is stated by every case that is
not about certification, rather than defaulted in the helper: a fixture that
quietly supplies the one fact a boundary checks is how the omission hole
lived.

One retained assertion needed a minimal change — `assert.deepEqual(row, ...)`
cannot hold against a null-prototype `node:sqlite` row under strict equality,
so it spreads the row. The property is exactly the reviewer's.

### Verification

- `cd v12 && npm test` — **269 pass, 0 fail**; zero test-owned roots retained.
- All four design models green: 64, 56, 74, 24.
- Eight mutations, seven bite; the eighth is recorded above.
- `pytest -n auto -m "not serial" tests/work` — **2975 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green**, with no failure belonging to another
Work.

### State

**Awaiting re-review of item 3a.** The rest of item 3 and all of item 4 are
still not implemented.

## Item 3a, second correction round — 2026-08-22

`review-2026-08-22T22-01-32Z.md`, three P1. All reproduced before any edit;
all correct. Evidence:
`evidence/correction-offer-claim-round2-2026-08-22.txt`.

**The review also closed something I had recorded as unwitnessed:** its two
deterministic public-path interleavings place acceptance between the stale
read and its terminal write, which is exactly the coverage I could not
construct for the issued-only CAS. Recording it rather than hiding it is what
got it covered.

### What I had wrong

**I fixed the sequential shape of a race and left the concurrent one — for
the second time.** The replay check moved before minting, and the DECIDING
replay stayed inside `transact`, after it. Two concurrent exact issuers both
pass the optimistic check; the winner commits, and the loser returned the
winner's record beside its own freshly minted bearer. That is the original
unusable pair, under exactly the concurrency the operation journal exists to
settle.

**TTL depended on the worker answering.** `expireOffer` was reachable only
from the late-decision branch, so an offer nobody answered held the per-Work
index forever with an unspent verifier. A bound that needs the holder of an
expired authorization to send one more message is not a bound.

**The issue signature omitted its authority binding**, so reusing an identity
against another authority read as an exact replay rather than a collision.

### Changed

The record `transact` returns is checked against the verifier this call's
bearer derives; a mismatch means this call lost, and the answer is a refusal
with no secret in it. `expireOverdue` is manager-owned time processing, at
reissue and at restart recovery. The full authority-scoped binding rides the
issue signature.

### One mutation is inert, and that is recorded

Making the sweep select `accepted` rows too changes nothing: `expireOffer`
goes through the issued-only CAS, so the row is selected, attempted and
refused. Two guards cover one property and the second neutralises the
mutation entirely — not a gap the suite missed, and not worth a test for a
difference that does not exist.

### Verification

- `cd v12 && npm test` — **279 pass, 0 fail** (274 before); zero test-owned
  roots retained.
- All four design models green: 64, 56, 74, 24.
- Six mutations, five bite; the sixth is the inert one above.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green**, with no failure belonging to another
Work.

### State

**Awaiting re-review of item 3a.** The rest of item 3 and all of item 4 are
still not implemented.

## Item 3a, third correction round — 2026-08-22

`review-2026-08-22T22-14-59Z.md`, one P1. Reproduced before any edit;
correct. Evidence:
`evidence/correction-offer-claim-round3-2026-08-22.txt`.

### What I had wrong, and the shape of it

I compared the returned durable verifier with the one this caller's bearer
derives. **Inequality proves a loss; equality proves nothing** — two exact
issuers can receive the same injected bearer, the inner one commits, the outer
replays that record, the comparison agrees, and the transaction LOSER reports
success. That makes effectively-once depend on a probabilistic property of the
secret source, when the journal is what decides it.

This is the third round on the same race, and my error has the same shape each
time: I keep answering "did this call win?" with evidence that is NEAR the
answer rather than the answer. First a check placed BEFORE the decision, then
a check that reads what the decision PRODUCED. The decision itself is the only
thing that knows.

### Changed

`transact` runs the action only when it did not replay, so the action setting
a flag IS the transaction boundary reporting which of the two happened.
Nothing about the payload is consulted for provenance.

The verifier comparison stays with a different job and a different refusal: if
this call did commit, the row it wrote must derive from the bearer it minted.
That is an invariant about a store defect, not a provenance decision.

### Verification

- `cd v12 && npm test` — **282 pass, 0 fail** (280 before); zero test-owned
  roots retained.
- All four design models green: 64, 56, 74, 24.
- Three mutations. The "always replayed" one fails **38** cases — every path
  that issues an offer — which is what load-bearing means.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### Two cases added, in both directions

A sequential exact reissue refused by the same marker, driven with the SAME
bearer so nothing about the payload distinguishes the calls; and a genuinely
first issue NOT refused as a replay, because a too-eager marker would satisfy
every refusal case above.

### State

**Awaiting re-review of item 3a.** The rest of item 3 and all of item 4 are
still not implemented.

## Item 3, second slice — activation and runtime start (2026-08-22)

`review-2026-08-22T22-21-52Z.md` **signed off item 3a**. This turn addresses
its non-blocking note and implements the next slice. Evidence:
`evidence/attempt-slice-2026-08-22.txt`.

### The note first

The re-review is right that my case titled "a SEQUENTIAL exact reissue is
refused by the same marker" is intercepted by the optimistic precheck and
never reaches the closure marker's branch — the title claimed branch evidence
the case does not provide. It is retitled to say exactly what it pins, and to
name which cases DO exercise the marker on each side. Citing a case for work
another case does is a quiet way to overstate coverage.

### What landed

Four rules, each ordered the way it is for one reason.

**Activation first.** The live assignment is compared field by field with the
one the claim recorded, and a stale or ended one is refused HERE — after one
writable call the same refusal would leave a runtime nobody is authorized to
own. The manifest is fixed once.

**Record before calling.** `start-requested` is durable before the adapter is
touched. Calling first and recording afterwards leaves a crash window with no
trace that a runtime may exist, and the next incarnation starts a second one.
Recording first can only over-report, which reconciliation resolves by
looking.

**Zero is not absence.** A retry needs positively proven absence; otherwise
the attempt waits as `uncertain`. Starting a second runtime for one
assignment is the failure this whole ordering exists to prevent, so the
ambiguous case costs a wait rather than a duplicate.

**Identification is by labels.** An id the adapter minted proves only that
something answers to it. Mismatch or multiplicity cancels, because two
runtimes under one assignment's labels means something already went wrong.

And `uncertain` never becomes `destroyed`: destruction is a fact about the
world, not the absence of an observation.

### A case of mine had to be corrected, and it is the interesting one

"Every declared value is reachable" walked the whole `execution_runtime` enum
in order — and that walk passes through `uncertain` straight into
`destroyed`, which the rule forbids. The case skips that step now, says why,
and reaches `destroyed` from a state that is not uncertainty. Writing the
reachability case and the refusal case separately would have hidden this: the
two rules meet exactly at that transition, and only walking the enum found it.

### Still not implemented

Cancellation ordering, output freeze, intake and cleanup — the rest of item 3
— and all of item 4. The adapter here is an injected object with two methods;
what a conforming adapter must BE is item 4's to pin, and this slice does not
pretend to have pinned it.

### Verification

- `cd v12 && npm test` — **295 pass, 0 fail** (282 before); zero test-owned
  roots retained.
- All four design models green: 64, 56, 74, 24.
- Seven mutations, each fails the case that names it.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting review of the activation and runtime-start slice.**

## The activation/runtime-start slice, corrected — 2026-08-22

`review-2026-08-22T22-34-55Z.md`, seven P1. All reproduced before any edit;
all correct. Evidence:
`evidence/correction-attempt-slice-2026-08-22.txt`.

### The common thread, before the list

The slice I passed was loose in several places at once, and they share a
shape: I wrote checks that were ABOUT the right thing without being BOUND to
it. An assignment that is live somewhere. An axis order that looks like a
sequence. A boolean that says a proof happened.

### What I had wrong

Activation accepted any free-standing attempt beside any live assignment,
ignored the session's participant, stored no assignment participant, compared
three of four fields on the fixed path, and left the participant out of the
runtime labels. `attempt.record` signed three of eight operands. Runtime start
had no journalled operation — a state label is not an effectively-once act.
Positive absence was a caller-authored boolean, which is the rejected
`schemaProven: true` shape a THIRD time. Attachment overwrote unconditionally
while a minted runtime with wrong labels was filtered away as uncertainty.
Enum order stood in for a transition order, so `completed` could advance to
`unable`. And monotonicity was a read/check/write race.

### Changed

Three things must agree before anything writable runs; all four assignment
fields are persisted, compared and labelled; the offer records the generation
its claim committed. Every durable operand rides each signature. One fixed
signed `runtime.start` operation commits before the adapter call and its
identity goes to the adapter. The retry path is CLOSED until item 4 defines
certified absence evidence. Attachment CASes null-or-identical, and a minted
runtime with wrong labels cancels before the filter — it is not absent, it is
wrong, and this call caused it. An explicit per-axis transition map, terminal
alternatives immutable, no public reset. Observations decided inside the write
against the expected value, journalled, with a concurrent writer refused as a
typed contract error rather than a raw SQLite one.

### Two model changes the review's own cases required

A cold start can discover anything: my first map allowed only
`not-started -> start-requested`, and the retained cases observe `running` and
`destroyed` directly. They are right — at restart the local axis is
`not-started` while a runtime may already exist, so reconciliation must record
what it FINDS rather than inventing a state nobody observed. The precondition
I added refusing reconciliation from a cold start was wrong for the same
reason and is gone.

### Four mutations passed at first, and each got a different answer

One was witnessable and is now witnessed: the session binding, whose retained
case is refused by the CLAIM guard first because its fixture has no claim.
Two are backed by the DECIDING guard while the JavaScript check is redundant —
the offer slice's lesson again — so a case now drives the attachment CAS from
a second connection. One is unwitnessable by construction and is recorded as
such: an attempt has exactly one claimed offer, so no reachable sequence
presents an `expect` that matches the claim and differs from the fixed value.

Four of my own earlier cases needed correcting too: three drove axes along
steps the per-axis map does not declare, and the enum-walk case walked the
vocabulary in array order — precisely what the review rejected.

### Verification

- `cd v12 && npm test` — **309 pass, 0 fail**; zero test-owned roots retained.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Cancellation, output freeze, intake and cleanup — and
all of item 4 — are still not implemented.

## The activation/runtime-start slice, second correction — 2026-08-22

`review-2026-08-22T22-53-46Z.md`, four P1 and one P2. All reproduced before
any edit; all correct. Evidence:
`evidence/correction-attempt-slice-round2-2026-08-22.txt`.

### The one I got most wrong

`claimOf` asked for one claimed offer with `.get()`, and
`offers.runtime_attempt_id` had no uniqueness constraint — so two Works could
reach `claimed` under one attempt identity and activation would pick between
them by unspecified row order.

**Last round I called that branch "unwitnessable by construction".** The
construction was a property of the ALLOCATOR, not of the store, and the store
is what activation reads. An invariant only the writer maintains is not an
invariant, and my claim was disproved by the retained store itself.

Corrected both ways the review asks: a unique index at the database boundary,
and a reader that fails closed for a store written before it. The fail-closed
branch is now witnessed rather than argued about — a case drops the index,
writes the second row and drives activation, because building the damaged
store the reader defends against is the only honest way to assert a defence
against damaged stores.

### The other four

The durable observation identity is resolved BEFORE the current-value
shortcut and the transition check: what a source identity already said is a
fact about that identity, and today's axis has no bearing on it. The
cancellation intent is reachable from every nonterminal runtime state, so one
ambiguous inspection cannot disable the response to stronger later evidence.
The attach identity carries the runtime — two attachments are two acts, and
one identity made the second read as a botched retry of the first — and a
lost race re-reads and preserves the fixed identity before cancelling. And
only a locked database is translated as contention: a wrong diagnosis is
worse than a raw error, because a caller can see that a raw error is
unclassified.

### Two mutation results recorded

**My first ordering mutation was not faithful.** It moved only where
`current` was read, which changes nothing, and it passed. The mutation that
matters moves the whole shortcut-and-transition block ahead of the durable
lookup, and it fails both retained cases.

**The attach-identity mutation is EQUIVALENT, not uncovered.** With the
identity keyed on the attempt alone, the journal collision is caught by the
same handler that catches the CAS refusal, and the code re-reads and cancels
— the same outcome by a different route. The runtime-scoped identity is still
right, but it is not what decides the outcome, so a case pins the other side
instead: attaching the same runtime twice answers "attached" and writes
nothing.

### One operational note

The schema comment I added contained backticks inside the SQL template
literal and terminated it. Caught by `node --check` before any test ran — the
second time this exact hazard has bitten me in this file.

### Verification

- `cd v12 && npm test` — **317 pass, 0 fail**; zero test-owned roots retained.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  codex-event-bridge 316/316; acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Cancellation, output freeze, intake and cleanup — and
all of item 4 — are still not implemented.

## The activation/runtime-start slice, third correction — 2026-08-22

`review-2026-08-22T23-07-46Z.md`, two P1 and one P2. Reproduced before any
edit — 320 tests, 317 passed, exactly the three additive cases failing. All
three findings correct. Evidence:
`evidence/correction-attempt-slice-round3-2026-08-22.txt`.

### The identity, from the other side

Last round I moved the durable `(attempt, incarnation, source_seq)` lookup
ahead of today's axis. But when no prior row existed AND the axis already held
the observed value, `observe` still returned success without writing anything
— so the identity stayed reusable and a different observation committed under
it. The conflict rule only bit when the first observation happened to change
state.

That is the same inversion as last round, arriving from the other direction:
**the identity's meaning must not depend on where the axis already was.** An
accepted sourced observation consumes its identity whether or not it moved an
axis. A manager-internal repeat stays inert, narrowly and deliberately — it
mints a fresh sequence at every call, so there is no identity for anyone else
to reuse and a row would record nothing that could be asked about.

### The fix that is not a transition

`stopping` was the one nonterminal state with no cancellation response. The
answer is NOT to declare `stopping -> cancel-requested`: that moves the axis
backwards to re-announce an intent the runtime is already carrying out. The
decision is what the caller acts on; the axis records where the runtime
actually is. Cancellation is idempotent for a stop already in flight.

`destroyed` is deliberately excluded and the code says so — it is terminal,
and an adapter still listing runtimes for a destroyed attempt is a
contradiction rather than a cancellation this manager can carry out.

### Measured, not assumed

The contention classifier read a substring of the free-form message, so a
trigger raising `busy provider invariant` inherited a database lock's meaning
and retry policy. I measured what this Node build actually throws: a trigger
abort is `errcode` 1811 (`SQLITE_CONSTRAINT_TRIGGER` — primary code 19 in the
low byte) with `errstr` "constraint failed"; a real lock is `errcode` 5 with
"database is locked". The classifier reads `errcode & 0xff` and accepts only
`SQLITE_BUSY` and `SQLITE_LOCKED`. No prose is consulted.

### Two mutation results worth reading

**M3 makes the reviewer's case pass.** Declaring `stopping ->
cancel-requested` still returns the `cancel` decision; only the case asserting
the axis is still `stopping` fails. That is precisely the distinction the
review drew, and it is now pinned on both sides.

**M5 disproved something I was about to claim.** I added a case driving a
genuine `SQLITE_BUSY` through `observe` because the classifier's positive side
looked unwitnessed. It was not — the round-2 case `a stale observer cannot
regress a newer axis value` already drives a real lock from a second
connection and fails under M5 too. Mine is a second, direct witness, recorded
as that rather than counted as new coverage.

### Verification

- `cd v12 && npm test` — **323 pass, 0 fail**; zero test-owned roots retained.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Cancellation ordering, output freeze, intake and
cleanup — and all of item 4 — are still not implemented.

## Item 3, third slice: cancellation ordering — 2026-08-22

The activation/runtime-start slice was signed off through item 3i
(`review-2026-08-22T23-21-33Z.md`), so this turn took the next named piece of
item 3. Evidence: `evidence/cancellation-slice-2026-08-22.txt`.

### The one rule

`session.cancel` FIRST. Until the generation is fenced the assignment is still
live, so a runtime stopped first is a worker torn out from under an assignment
the authority still believes is executing. Fence, then stop.

The manager's own intent is journalled BEFORE the authority is asked — the
same discipline as runtime start, for the same reason: a crash between the two
boundaries must be answerable, and a state column records only that somebody
once intended to cancel.

### What the ordering costs to test

**Final state cannot express it.** A manager that stopped the runtime and then
fenced leaves exactly the same rows behind as one that fenced and then
stopped. So the session and adapter doubles write into one shared trace and
the cases assert the sequence.

And a real `V12Authority` drives the whole path once: real claim, real
`V12Session.cancel`, the authority's own `runtime-quiescence:<generation>`
token. A double can agree with an implementation about a shape neither shares
with the authority.

### What is deliberately closed

**The quiescence gate this installs is not satisfied here.** Measured against
the current tree rather than the prose, `Core.satisfyGate` accepts only
`runtime-absent` evidence naming the exact runtime, or a certified-isolation
policy. `runtime-absent` is the same positive-absence claim the reconciliation
retry path is closed for until item 4 defines certified adapter evidence —
opening it here while that stays closed would be two answers to one question.
Agent-side quiescence is not that evidence and never becomes it.

### One distinction that looks like a contradiction and is not

`cancel()` — the reconciliation helper — reports a DECISION about what an
inspection found, and a destroyed attempt contradicts it, so it still refuses
(the round-3 rule, signed off). `requestCancellation` PERFORMS a cancellation
at the authority, and a destroyed runtime merely leaves nothing to stop.
Different acts, different rules; both keep the axis where the runtime is.

### One fixture defect caught before it hid anything

The first `running(...)` fixture started a runtime the adapter never listed,
so nothing attached and every ordering case passed while stopping nothing. It
asserts the attachment now.

### Verification

- `cd v12 && npm test` — **335 pass, 0 fail**; zero test-owned roots retained.
- Nine mutations, all nine witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** Output freeze, intake and cleanup — and all
of item 4 — are still not implemented.

## The cancellation-ordering slice, corrected — 2026-08-22

`review-2026-08-22T23-40-54Z.md`, two P1 and one P2. Reproduced before any
edit — 336 tests, 335 passed, the reviewer's stopped-fact regression the sole
failure. All three correct. Evidence:
`evidence/correction-cancellation-slice-2026-08-22.txt`.

### The one I left out

The acceptance says the manager orders **agent cancellation and runtime stop**
after the fence. I built the runtime half and marked the item done.
`session.cancel` is the assignment-authority fence; it is not the provider
agent's cancellation, and nothing in the slice touched an agent at all.

What went wrong is worth naming: **I let the item-4 boundary swallow more than
it owns.** Item 4 owns what a conforming agent must BE. Where its cancellation
sits in the order is item 3's — and that is the whole subject of this slice,
so deferring it deferred the thing being built.

The agent is an injected boundary now, exactly as the runtime adapter is, and
it is ordered between the fence and the stop. It goes first because an agent
told to stop after its runtime is already going away never hears the order,
and the cooperative shutdown is the only thing asking it buys over a kill.

The parameter order is the act order, and two adjacent injected objects are
easy to swap, so both shapes are checked and a swap refuses.

### Reaching a boundary is not evidence of its effect

`orderStop` discarded `adapter.stop`'s answer and reported `stopped: true`
whenever the call returned. That is the caller-authored `absenceProven`
mistake again, arriving from the manager's own side this time.

The word `stopped` is gone from the answer. The manager reports `ordered` —
what it knows — and passes each settlement through uninterpreted. Positive
quiescence arrives as an observation or not at all.

### My plan text was wrong, not the code

Item 3k said the stop order is not repeated for a runtime already `stopping`;
the code repeats it and my own regression requires the repeat. The AXIS is not
rewound; the ORDER is re-issued under the same operation identity, because an
order that may have been lost must be repeatable. The plan states that now and
carries a dated correction note, so the chronology shows the contradiction and
its resolution.

### Verification

- `cd v12 && npm test` — **339 pass, 0 fail**; zero test-owned roots retained.
- Five mutations, all five witnessed; O3 fails the reviewer's retained case
  and mine together.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Output freeze, intake and cleanup — and all of item 4
— are still not implemented.

## The cancellation-ordering slice, second correction — 2026-08-22

`review-2026-08-22T23-55-38Z.md`, one P1. Reproduced before any edit — 340
tests, 339 passed, the reviewer's post-fence failure regression the sole
failure. Correct. Evidence:
`evidence/correction-cancellation-round2-2026-08-22.txt`.

### I created this last round

I added the agent boundary in front of the runtime stop and did not ask what
happens when the boundary I put first fails. A throwing agent left the
function before the stop was ordered — with the authority already fenced and
the assignment already ended — so an unreachable provider left a fenced
runtime running indefinitely.

**A cooperative request is the polite path, not a precondition for the
forceful one.** Persistent agent unreachability is a reason to stop the
runtime, not a reason to leave it alone. The failure is captured, the stop is
ordered anyway, and only then is the failure re-thrown unchanged — the order
stays agent-before-runtime and the classification stays the caller's.

**When both fail, neither hides the other.** An `AggregateError` carries both
in call order. Letting the runtime's failure propagate alone would have been
this boundary silently choosing which failure the caller is entitled to see —
the same shape as summarizing a settlement.

### One mutation is equivalent, and it caught a title of mine

P4 — a failed agent still reports a settlement — changes nothing reachable,
because the failure path throws before the return and the assignment is dead
code. Recorded as equivalent rather than counted.

It also showed that one of my case titles was overclaiming: it said "reports
no settlement" when no settlement is observable on that path at all. Retitled
to what it pins — the failure is re-thrown unchanged, after the stop was
ordered.

### What is still not durable, said plainly

A failed agent cancellation is visible to the caller and is **not** recorded
in the store. There is no agent-session evidence table yet — store surface
item 7, owned by item 4 — so a manager that crashes right after the throw
learns nothing about the failed cooperative attempt beyond the committed
`attempt.cancel` intent. A gap in coverage, not a claim that it does not
matter.

### Verification

- `cd v12 && npm test` — **342 pass, 0 fail**; zero test-owned roots retained.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Output freeze, intake and cleanup — and all of item 4
— are still not implemented.

## The cancellation-ordering slice, third correction — 2026-08-23

`review-2026-08-23T00-05-09Z.md`, one P2. Reproduced before any edit — 343
tests, 342 passed, the reviewer's sentinel regression the sole failure.
Correct. Evidence:
`evidence/correction-cancellation-round3-2026-08-23.txt`.

### A value that also means absence

`agentFailure = null` meant both "nothing was thrown" and "`null` was thrown",
and JavaScript lets a boundary throw any value. An agent that threw `null` had
its failure silently dropped — the stop was still ordered, but the caller got
an ordinary answer and a simultaneous runtime failure lost its partner. Both
of last round's claims were false for exactly that value.

Presence is its own fact now: a boolean carries it, the variable carries only
the thrown value.

### The part worth keeping

**This codebase already knew this.** `ControlStore.replay` carries a review
note from an earlier round saying the same thing in the same words — it
answered `null` for both "no row" and "the committed result was JSON null",
and the correction was that presence is its own fact. I wrote the identical
defect three modules later. The lesson had been recorded and not generalized.

### One more of the same shape, found by sweeping

`agentSettlement = agent.cancel(...) ?? null` collapsed "the boundary returned
nothing" into "the boundary returned null" — the same mistake one size
smaller, and it contradicted the comment directly above it claiming the
settlements are un-summarized. Both settlements are verbatim now. Recorded as
my own sweep, not as a review finding, because it is not one.

### Verification

- `cd v12 && npm test` — **346 pass, 0 fail**; zero test-owned roots retained.
- Four mutations, all four witnessed. Q2 — swapping the sentinel to
  `undefined` — exists because moving the defect is not fixing it, and only a
  case that throws `undefined` sees the difference.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Output freeze, intake and cleanup — and all of item 4
— are still not implemented.

## Item 3, fourth slice: the output freeze — 2026-08-23

The cancellation-ordering slice was signed off with no findings
(`review-2026-08-23T00-13-56Z.md`), so this turn took the next named piece.
Evidence: `evidence/freeze-slice-2026-08-23.txt`.

### The store transition and the validation, and nothing else

W2930 owns filesystem and OCI collection; W2929 owns the immutable store
transition and the validation of what the adapter sealed. Schema 3 → 4 adds
`outputs` (one row per attempt, and the PRIMARY KEY says so) and
`output_artifacts`.

### Gone is not finished

`destroyed` is not quiescence. A seal describes a tree that has stopped
changing, and a writer nobody watched stop never produced an observation that
its tree had. `uncertain` is a failure to look. Only a positive `quiescent`
observation passes, and the refusal uses the code already pinned for exactly
this question — `runtime-observation.quiescence-unknown`.

### The disposition is compared, not accepted

A turn's outcome *gates* the worker disposition and never chooses it, and turn
records are item 4's. So freeze requires a terminal disposition to be already
RECORDED and requires the declaration to equal it — a comparison against
durable state rather than a caller's assertion about a turn nobody here can
see. Then the sealed document must say the same thing: three places must
agree, because two agreeing is how the third gets in.

### The liveness read is only a read, and the code says so

The authority is a different store, so nothing here can make "still live" and
"recorded frozen" one atomic fact. The read runs inside the freeze transaction
so the window is as small as it can be, and the design does not depend on it
being zero — material from an assignment that ended anyway is quarantined at
intake, which is the next slice.

### The identity is the act; the signature carries the bytes

The record operation is fixed per attempt, not per digest. If it varied with
the bytes, two different results would be two different operations and both
would commit — the opposite of an immutable record. `recordFrozenResult`
therefore admits `frozen` as well as `freeze-requested`, so a manager that
crashed after recording replays rather than hitting a precondition that would
hide the collision.

### One equivalent mutation, and one fixture defect

R11 — trusting the declared digest instead of recomputing — is **equivalent**,
because `validateManifest` has already refused any document whose declared
digest does not recompute. The recomputation stays for provenance, and the
comment now says that instead of implying a guard.

And the first `quiesced(...)` fixture drove the execution axis "until it
matches", which silently reached a different state for `uncertain`. It walks a
declared route per target now.

### Verification

- `cd v12 && npm test` — **370 pass, 0 fail**; zero test-owned roots retained.
- Twelve mutations, eleven witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** Intake and cleanup — and all of item 4 — are
still not implemented.

## The output-freeze slice, corrected — 2026-08-23

`review-2026-08-23T00-30-49Z.md`, four P1. Reproduced before any edit — 372
tests, 370 passed, the two additive regressions the only failures. All four
correct. Evidence: `evidence/correction-freeze-slice-2026-08-23.txt`.

### The two I built wrong

**The freeze signature was ignored.** I computed the exact operation
signature, journalled it, and then passed only the ID to the adapter and
compared only the ID when the result came back — so any schema-shaped digest
was accepted. The id is the retry key; the signature is the binding over the
kind and every operand. My own fixture supplied `digest("freeze")`, unrelated
to the journalled operation, and every case stayed green.

**Exact replay was hidden by later output state.** The axis precondition ran
before the fixed record identity, so once `output` advanced to `sealed` an
exact retry refused as a precondition instead of replaying the journal. **That
is the observation-ordering defect a third time, in a third module** — and
twice now this Work has recorded the lesson where it was learned and not
carried it. A note in the module where a defect was found does not protect the
module where it is written next.

### The two I never built

**A digest is not a record.** The store held `attempt.input_digest` and
`outputs.manifest_digest` and not one byte of either document, so freeze could
not compare a sealed result against the output declarations, and intake,
publication and restart were left with a number and nothing to replay.

One table answers both, because both are the same fact: a validated document
this manager is holding, keyed by the digest that identifies it. Retention is
idempotent by construction — the key is computed from the bytes — and a digest
that would name different bytes is refused rather than overwritten.
`loadManifest` parses fresh, because a cached object handed to two callers is
a durable record one of them can edit for the other.

The declared-output comparison runs **both ways**: every result output must be
declared, and every declaration must be answered — a declaration dropped from
the result is a question the result pretends was never asked. The
required-output rule is conditioned on the disposition, because the pinned
sentence has two halves and the inability half is a requirement too.

### My fixture had to change to mean anything

`INPUT` was `digest("input")` — a number naming no document — which is exactly
why nothing could be compared against a declaration. It is the retained input
manifest's own digest now, and the fixture retains the declaration each case
actually names.

### Verification

- `cd v12 && npm test` — **385 pass, 0 fail**; zero test-owned roots retained.
- Fourteen mutations, all fourteen witnessed. S9 is worth reading: it makes
  the STRICTER rule and is still wrong.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Intake and cleanup — and all of item 4 — are still not
implemented.

## The output-freeze slice, second correction — 2026-08-23

`review-2026-08-23T00-49-18Z.md`, four P1. Reproduced before any edit — 389
tests, 385 passed, the four additive regressions the only failures. All four
correct, and all four about **trust in what was already stored**. Evidence:
`evidence/correction-freeze-round2-2026-08-23.txt`.

### Being at the named key is not being the named thing

`loadManifest` parsed the row and handed it back. Nothing said the body was
the KIND the caller needed, so a retained result manifest — a perfectly valid
thing to retain — could be named as an attempt's `input_digest` and its
similarly shaped output rows read as trusted declarations. Every public
operation in that sequence is valid on its own; the boundary that had to
refuse the combination did not exist.

I introduced this in the same round that introduced retention: I wrote the
loader as a getter and treated validation as something that happens on the way
IN. A guard on the way in cannot see a document put there by a different,
equally legitimate call.

The definition is required rather than defaulted now, the body is validated as
that definition, and its digest is recomputed against the key it was filed
under.

### One rule, one place

`retainManifest` refuses an existing key with different bytes; the result path
wrote `INSERT OR IGNORE` and skipped it, so the `outputs` row could commit a
foreign key to another document's bytes while the operation reported success.
Writing a rule in one function does not apply it to another writer of the same
table. Both go through `retainCanonical`.

### The same lesson one round later and one line higher

Last round I moved the output-axis check behind `store.replay`. The
DECLARATION lookup stayed in front of it, so removing the old input row made
an exact retry refuse. **I moved the check the review named instead of the
boundary the rule is about.** The immutable identity and signature are
computed first and replay resolved there; everything about today applies only
to a genuinely new record.

### Declared limits

`max_bytes` against the content total (or the artifact's declared size when
there is no tree), `max_entries` against the entry count, and the media type
against the allow-list — literally, including an empty one, because an
allow-list that permits everything when it names nothing is a fail-open
reading of a rule written to close.

### One mutation improved the code

T9 — measuring an absent output — was inert, because a null tree and a null
artifact skipped every measurement anyway. But the schema PERMITS
`missing-optional` beside an artifact, and that is a document contradicting
itself. The branch refuses the contradiction now instead of quietly declining
to measure it, and then the mutation bit.

### Verification

- `cd v12 && npm test` — **396 pass, 0 fail**; zero test-owned roots retained.
- Nine mutations, all nine witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Intake and cleanup — and all of item 4 — are still not
implemented.

## The output-freeze slice, third correction — 2026-08-23

`review-2026-08-23T01-02-53Z.md`, one P1. Reproduced before any edit — 397
tests, 396 passed, the reviewer's regression the only failure. Correct.
Evidence: `evidence/correction-freeze-round3-2026-08-23.txt`.

### The same defect again, in the other direction

Last round I refused an output that says `missing-optional` while carrying
material, and did not refuse its converse. So a `present` output with neither
a tree nor an artifact skipped every limit and satisfied a REQUIRED
declaration under a `completed` disposition. A status word is not material.

**This is the second time in two rounds that I enforced one direction of a
two-directional rule** — and I wrote "a comparison that runs one way is half a
comparison" into this dossier one round earlier, about this same function.
Recording the lesson beside the code did not make me apply it to the very next
branch I wrote.

Corrected to the contract rather than to the minimum that passes the case.
§8.4: a frozen result binds "every declared output's content/tree digest AND
artifact reference". Both are required for a present output; the nullable
members exist so a missing output can say so.

### An inert branch the correction exposed, and closed

With both representations required, the size fallback — the tree's total, or
else the artifact's declared size — became unreachable. That is the inert
guard shape I recorded last round, so it became a decision rather than a
deletion: **both** sizes are bounded now. Measuring only the tree would leave
the transported representation unbounded.

### Verification

- `cd v12 && npm test` — **399 pass, 0 fail**; zero test-owned roots retained.
- Three mutations, all three witnessed. U2 satisfies the reviewer's case while
  accepting an output that supplies only one half, which is why my case drives
  each half separately.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Intake and cleanup — and all of item 4 — are still not
implemented.

## Item 3, fifth slice: trusted intake and cleanup — 2026-08-23

The output-freeze slice was signed off with no open finding, so this turn took
the last named piece of item 3. **Item 3 is now implemented end to end.**
Evidence: `evidence/intake-cleanup-slice-2026-08-23.txt`.

### Two design decisions that are the slice

**`recordIntake` is not given a session.** "Never publishes on the dead
generation" is a rule about what intake may do, and the strongest way to keep
it is to hand this boundary no way to reach the authority at all. A handle
passed and not used is a rule enforced by good intentions — and this Work has
already found two rules that were only enforced by their writer.

**The discard path is closed.** SPEC 6.4 admits destruction under a "pinned
discard policy" as well as a satisfied intake boundary, but a policy taken as
an argument is the rejected `absenceProven` shape a fourth time. Destruction
requires a recorded intake decision and the refusal names what would open it —
the same closure the retry path already has.

And retention is **two facts**: whether intake wanted the material and where
the material went are separate columns, because a rejected draft that is
retained under policy is an ordinary outcome.

### Why the cleanup identity is derived from intake

The pinned rule is that the `blocked-on-intake` refusal "is durable to its own
operation; a later re-evaluation uses a new operation". A counter would
satisfy the words and be caller-authored. So the identity is derived from the
intake state it was evaluated against: a retry while nothing has changed
replays the same refusal, and once intake decides the identity moves. The
evaluation is keyed on the durable fact whose change makes re-evaluating
legitimate.

### Ordered, not done — again

`requestDestroy` passes the adapter's settlement through uninterpreted and
moves the cleanup axis only on a positive `destroyed` observation. And
destruction waits for the assignment to be over, because destroying the
runtime of an assignment the authority still believes is executing is the
cancellation ordering defect from the other end.

### One unfaithful mutation, recorded

V6's first attempt disabled **one disjunct of a four-way condition** —
`false && A || B || C || D` still fires on the rest — so the clause the case
drives was untouched and it passed. The faithful mutation disables the whole
condition, and it fails.

### Verification

- `cd v12 && npm test` — **415 pass, 0 fail**; zero test-owned roots retained.
- Ten mutations, all ten witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** Item 4 is untouched, and it still owns the
two things this manager deliberately refuses to decide: certified evidence of
runtime absence, and what a conforming agent or runtime adapter must be.

## The intake/cleanup slice, corrected — 2026-08-23

`review-2026-08-23T01-29-05Z.md`, three P1 and one P2. Reproduced before any
edit — 419 tests, 415 passed, the four additive regressions the only failures.
All four correct. Evidence:
`evidence/correction-intake-cleanup-2026-08-23.txt`.

### The one that invalidated my own fixture

`recordIntake` required only a fixed assignment and stored an unbound locator,
and the row carried no result digest. So **the slice's own `ended()` fixture —
which created no output row and no retained result manifest — accepted,
rejected, retained and quarantined material that did not exist.** Every
positive case in the suite was about nothing.

A locator is where something is. It is not which immutable result was judged,
and a restart holding only a locator cannot say what the decision concerned.

Corrected both ways: intake requires a sealed output and binds the decision to
that output's result-manifest digest, with a foreign key to the retained
bytes. And the fixture drives the real freeze path now — a real declaration, a
real sealed result, `requestFreeze` — so the positive cases decide the fate of
material this manager actually sealed.

### A summary that omits a column is not a guard over that column

`reason` went straight into SQLite. The shared transaction guard scans the
serialized *result*, and my result deliberately omitted `reason`, so a live
bearer passed as prose committed verbatim. The exact durable record is
assembled and scanned before any of it is written.

### Absence does not decide policy

`settleCleanup` asked only whether the runtime was `destroyed`, so cleanup
could complete with no intake decision at all. An observation proves the
runtime is gone and says nothing about whether the ended assignment's material
was retained or quarantined. Two gates now, rather than one gate doing two
jobs.

### A deadline is a deadline or it is not one

The interface and the contract both call `retainUntil` a deadline and the
STRICT column constrained only its storage class, so the literal `tomorrow`
was durable scheduling state. It is validated against the canonical timestamp
form; no expiry policy is decided here.

### Verification

- `cd v12 && npm test` — **423 pass, 0 fail**; zero test-owned roots retained.
- Five mutations, all five witnessed. W2 is blunt and recorded as such: the
  foreign key is the deciding guard and takes most of the suite with it, so
  the narrower claim is pinned by a case that compares the recorded digest
  against the `outputs` row.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** All of item 4 remains, plus the quarantine manifest
for material with no frozen result.

## The intake/cleanup slice, second correction — 2026-08-23

`review-2026-08-23T01-43-26Z.md`, two P1. Reproduced before any edit — 425
tests, 423 passed, the two additive regressions the only failures. Both
correct. Evidence: `evidence/correction-intake-round2-2026-08-23.txt`.

### The same ordering rule, in a fourth module

`recordIntake` read the `outputs` row and refused its absence before reaching
the journal. But a committed decision already owns the exact result digest and
keeps its manifest alive, so dropping the redundant output index turned an
exact retry into a precondition failure and hid a changed one instead of
colliding.

**This is the fourth time**: `ControlStore.replay`, `observe`,
`recordFrozenResult`, and now `recordIntake`. Each time the fix was "resolve
the durable identity before consulting today's state", and each time I wrote
the next module with the precondition first.

The shape of the fix is what makes it hold: an existing decision already names
its material, so the output index is consulted **only** when there is no
decision to replay — exactly the case in which nothing can be hidden by
requiring it.

### A foreign key proves existence, not identity

`intakeOf` validated the four assignment fields and returned every other
column as trusted. The foreign key proves that *some* retained manifest
exists; it does not prove this is the result the decision committed.

The journal is the independent witness, and it survives even when the current
output index does not. The row's own columns are reassembled into the exact
durable record, its signature recomputed and compared against the committed
operation — with writer and reader building that record in one place, so the
two signatures are the same computation rather than two that agree today. A
mismatch is `integrity.digest`, not `operation-collision`: a row disagreeing
with its own committed decision is not a caller reusing an identity.

### One mutation is masked, and the measurement is the point

X4 — dropping the typed result load — changes nothing reachable, because the
signature authentication already catches a changed digest. Removing either
guard alone leaves the other covering the case; only removing **both** makes
it fail. So the typed load the review asked for is kept and is not counted as
witnessed coverage, and the case that drives it is titled "TWICE OVER" with
the measurement written beside it.

### Verification

- `cd v12 && npm test` — **428 pass, 0 fail**; zero test-owned roots retained.
- Five mutations, four witnessed and one measured as masked.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** All of item 4 remains.

## Item 4, first slice: certifying one agent-session profile — 2026-08-23

Intake/cleanup was signed off, completing item 3. Evidence:
`evidence/agent-profile-slice-2026-08-23.txt`.

### The sign-off's clarification, closed in code

The reviewer recorded that "writer and reader build the record in one place"
was **not literal** — the writer assembled its own operand object beside
`intakeRecord`, so the invariant was true of the signature formula rather than
of the code. They were right to record it instead of letting the stronger
claim stand, and the honest response is to make the claim true rather than to
weaken it. `recordIntake` builds its operands through `intakeRecord` now, so
adding a column changes both sides or neither.

### Shape, seal, policy — and only what the schema cannot say

Shape first, because every later rule reads members. Seal second, because a
policy decision about a document whose bytes do not match its own digest is a
decision about something nobody agreed to. Policy last, and only the rules the
schema cannot state.

### Where the deciding guard actually is, measured

The policy rule is that the two postures carry different pinned policies.
**Measured: the two families are refused by different guards.** The codex
branch of the schema pins consent and execution to two different policy
definitions, so equal policies are unrepresentable and the shape check answers
first. The ACP branch pins both to one definition with a free-form
`session_mode_id`, which the schema cannot compare — and that is exactly the
gap the policy rule closes.

My first version of that case asserted the policy refusal for both families
and failed on the codex half. It asserts what actually decides for each now,
and says why: claiming my rule decides where the schema already did would have
been a claim the schema was quietly satisfying.

### The fixtures are the design model's own

Both profiles are copied verbatim from the ACP boundary's `traces.json`,
including their `document_digest` — and both recompute exactly under this
manager's RFC 8785 canonicalization, measured before the suite was written. So
the seal these cases check is the design's, not a number the suite produced
and then agreed with.

### Verification

- `cd v12 && npm test` — **437 pass, 0 fail**; zero test-owned roots retained.
- Six mutations, all six witnessed; Y3 is the ordering itself.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** The rest of item 4 remains: the separate
consent and execution sessions with per-posture epochs, turns and deadlines,
event normalization, and the adapter contracts.

## The agent-profile slice, corrected — 2026-08-23

`review-2026-08-23T02-12-31Z.md`, two P1 and one P2. Reproduced before any
edit — 441 tests, 439 passed, the two additive regressions the only failures.
Both correct, and both are the same mistake: **I built a new door and left the
old one open.** Evidence:
`evidence/correction-agent-profile-2026-08-23.txt`.

### A composing entry point a caller may decline to call is a suggestion

`certifyProfile` took `kind` as an operand, accepted `agent-session`, and
wrote a caller-authored digest straight into the same table — so the shape,
seal, posture-policy and secret checks I had just built were avoidable by not
calling the entry point that performs them.

### "Certified" without a kind is a question with no single answer

`certifiedProfile` asked only for the digest, so a genuinely certified
agent-session profile satisfied `issueOffer`'s runtime check. The two are
separate contract axes with separate schemas, seals and policies; a digest
certified under one is not certification under the other **even when the bytes
are genuine**.

### One place I did not do what the case implied, and why

The review's forge case calls the generic writer and then asserts the lookup
reports false, which reads as "drop the operand silently". I refused the
operand instead and kept their assertion underneath a `throws`.

The reason is a hazard in the other reading: silently dropping a supplied
`agent-session` would satisfy the case while writing the caller-authored
digest as a certified **runtime** profile — turning an attempted forgery into
a successful one on the axis the caller never named. The case would pass and
the store would be worse. A case of mine also asserts that a refused kind
certifies nothing, on either axis.

I said on the thread that I would rather be overruled than have quietly
reinterpreted their case.

### Verification

- `cd v12 && npm test` — **443 pass, 0 fail**; zero test-owned roots retained.
- Four mutations, all four witnessed. Z3 closes the cross-axis hole in the
  other direction and immediately breaks the axis itself, which is why a case
  drives a runtime profile certifying a runtime offer rather than only
  checking that an agent one cannot.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** The rest of item 4 remains.

## Item 4, second slice: opening an agent session — 2026-08-23

The profile-certification slice was signed off, so this turn took the next
piece. Evidence: `evidence/agent-session-slice-2026-08-23.txt`.

### The profile bytes, before the review had to ask

Certification recorded a digest and no document, and a session must pin the
per-posture policy the profile carries. That is the freeze review's lesson —
**a digest is not a record** — applied before it could be found a second time.
The certified bytes are retained, and the loader re-validates them and re-binds
them to the key they are filed under, because a guard on the way in cannot see
an edit made afterwards.

### The three rules

**A fresh epoch per posture**, decided by the store as the next epoch for this
`(attempt, posture)`. There is no resume, fork or promote path, so the
derivation says so rather than a comment saying so, and the two postures count
separately because they never share a connection.

**The posture bindings are read from the certified profile**, not restated —
a rule restated in two places is a rule that can disagree with itself. What
this slice adds is the cross-field rule the frozen schema's own description
says JSON Schema cannot express: an execution session's assignment belongs to
the session's Work.

**No Baton capability, by construction.** The boundary takes a store, an
attempt id, a posture and a profile digest — no session, no token, no
authority handle. Same move as `recordIntake` taking no session, and for the
same reason.

### Two things recorded rather than smoothed over

**A2's first mutation was not faithful**: `MAX + 0 + 1 - COUNT + COUNT` is
arithmetically the original, and it passed for that reason. A mutation that
computes the same number is not a mutation.

**One case of mine was too blunt.** The capability check first forbade the
substring `authority` and failed on `authority_uuid` — a Work reference column
that is not a capability at all. A guard that refuses legitimate names is not
a stricter guard, it is a broken one.

### Verification

- `cd v12 && npm test` — **453 pass, 0 fail**; zero test-owned roots retained.
- Seven mutations, all seven witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** Turns and their deadlines, event
normalization and the adapter contracts remain.

## The agent-session slice, corrected — 2026-08-23

`review-2026-08-23T02-36-51Z.md`, three P1. Reproduced before any edit — 456
tests, 453 passed, the three additive regressions the only failures. All three
correct, and the third corrects a mistake about the DESIGN rather than just
the code. Evidence: `evidence/correction-agent-session-2026-08-23.txt`.

### I conflated two roles, and my own test defended the hole

`openAgentSession` consulted only the assignment cached in the manager's
attempt row, so an execution session opened cleanly against an assignment the
authority had already fenced and ended.

**The reason I built it that way was a case I wrote myself.** I asserted "no
Baton capability" of the function *signature* — no session, no handle — and
called that keeping the rule by construction. It conflated the trusted Worker
Manager, which **is** the one Baton authority client and must reproject, with
the untrusted agent endpoint and relay, which are what must never receive a
capability. Removing the manager's handle did not prove provider isolation; it
removed the liveness check the contract requires.

A structural test can encode a misunderstanding as firmly as it encodes a
rule.

The handle is a parameter now, read once, and the rule it replaced is stated
where it actually lives: the handle appears in nothing the function returns
and in no column of the durable row — and a case asserts the handle **was
used**, because a reprojection that never happened would satisfy an absence
test perfectly.

### Freshness and concurrency are two rules

I allocated `MAX + 1` and inserted unconditionally, so a posture could hold
three simultaneously open epochs — and my freshness case opened exactly that
and called it evidence. A partial unique index decides it now, driven from a
second connection, because a read of MAX followed by a separate insert is not
an atomic allocator. `closeAgentSession` is the only thing that frees a
posture; `unknown` deliberately does not.

### Two of three witnesses agreeing is not agreement

The loader destructured `document_digest` away and never compared it, so a
retained profile could carry somebody else's well-formed seal. Declared,
recomputed and the key are one fact now.

### A habit I have now made twice

The handle case's forbidden-substring list rejected `participant` — the
assignment's own identity, not a capability — which is the same too-blunt
guard I recorded one round ago after forbidding `authority` and failing on
`authority_uuid`. Twice is a habit; the note is in the case now, not only in
the evidence.

And the backtick hazard bit a **third** time in the schema template literal,
caught by `node --check` before any test ran.

### Verification

- `cd v12 && npm test` — **458 pass, 0 fail**; zero test-owned roots retained.
- Six mutations, all six witnessed. B2 fails the liveness case *and* the
  handle case, which is the point.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Turns, event normalization, the adapter contracts and
the re-identification gate remain.

## The agent-session slice, second correction — 2026-08-23

`review-2026-08-23T02-51-57Z.md`, one P1. Reproduced before any edit — 459
tests, 458 passed, the reviewer's regression the only failure. Correct.
Evidence: `evidence/correction-agent-session-round2-2026-08-23.txt`.

### Where I had already written the answer

`openAgentSession` checked only that the handle could *answer* — that it had
`assignmentOf` — and that projection is Work-scoped. A session genuinely
minted for `poc.gemini` returns the same live assignment, whose participant is
`poc.claude`, and the four-part comparison then proves the projection and the
attempt agree while proving nothing about who asked.

**The activation slice already carries this exact lesson, in a comment I
wrote:** the claim says which assignment this attempt won, the binding says
who is asking. I re-derived only one of the two here — in the module I had
just corrected for the neighbouring half of the same rule.

### One measurement recorded rather than claimed

I read the binding into a local and called it *snapshotted*. Measured: the
local is **equivalent**. A mutation reading `session.participant` inline
changes nothing reachable, because the value is used exactly once and what
lands in the durable row comes from the attempt, never from the handle. The
local is kept — the single read stays visible — but the comment says that now
instead of implying a guard, and the case that drives a mutating getter is
titled for what it pins.

### One shadowed identifier, caught before it could matter

My first version named the local `binding`, which shadows the *posture*
binding already in scope, inside the one block where the two are easiest to
confuse. Renamed, with the reason beside it.

### Verification

- `cd v12 && npm test` — **461 pass, 0 fail**; zero test-owned roots retained.
- Three mutations, two witnessed and one measured. C3 is the other direction
  and matters: a consent session exists before any claim, so requiring a
  handle for it would be requiring proof of something that does not exist yet.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Turns, event normalization, the adapter contracts and
the re-identification gate remain.

## Item 4, third slice: the turn and its outcome — 2026-08-23

The session-opening slice was signed off, so this turn took the next piece.
Evidence: `evidence/agent-turn-slice-2026-08-23.txt`.

### Selected, never inferred

The ACP boundary lists what an outcome is *not* derived from: silence,
transport closure, an empty update stream, a tool call's own status, agent
prose, reachability at any layer. Each is a guess somebody could defend, which
is why the section exists. So the selector takes the evidence a relay actually
holds and **refuses** when none of it names an outcome.

**The order of precedence is an argument, not a convenience.** A §4 violation
ends the turn where it happens, so it outranks anything arriving afterwards. A
terminal fact outranks an elapsed deadline because the fact *arrived*.
Transport death outranks the deadline for the reason it is a separate outcome
at all: the epoch is gone, which is more than "nothing has come back yet".

### Gates, never chooses

The acceptance table is transcribed verbatim and driven **exhaustively** —
all eight rows, both directions — because a closed vocabulary tested at three
of eight points is a closed vocabulary nobody has checked. `cancelled` and
`policy-failed` permit nothing because the assignment is already ended;
`timeout` and `transport-lost` permit nothing because they say the relay does
not know, and a disposition accepted on "I do not know" is the forbidden
inference wearing a different hat.

The permitted set is stored beside the turn rather than re-derived on read, so
a later reader sees the gate that was *applied*.

### Verification

- `cd v12 && npm test` — **474 pass, 0 fail**; zero test-owned roots retained.
- Eight mutations, all eight witnessed. D2 and D3 keep every individual
  mapping and only reorder the precedence, and both fail: an ordering that is
  only a comment is not an ordering.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting independent review.** Event normalization, the adapter contracts
and the re-identification gate remain.

## The turn slice, corrected — 2026-08-23

`review-2026-08-23T03-15-42Z.md`, five P1. Reproduced before any edit — 480
tests, 474 passed, the six additive regressions the only failures. All five
correct. Evidence: `evidence/correction-agent-turn-2026-08-23.txt`.

### My test defended my mistake, again

§10.3 maps `turn/completed` status `failed` to `agent-failed`. I had two
statuses and my own case asserted that `failed` must be **refused**. A
vocabulary I shortened is not a stricter vocabulary — it is a different one,
and the difference was invisible because I also wrote the test that defended
it. That is the second time in three rounds.

And the refinement branch collapsed every `codex-error-info` string to
`agent-failed`, dropping §10.6 entirely. That table is transcribed in full now
— eleven rows, each with an outcome *and* the closed error pair it is reported
as — and driven exhaustively, because sampling three of eleven leaves eight
untested and the table looking driven.

### One place I have not done what the review asked

The review says an unrecognized `codexErrorInfo` must refuse. §10.6 ends: "the
raw `codexErrorInfo` string is retained as untrusted diagnostics; it selects
nothing beyond this table, **and an unrecognized value takes the last row**."
Refusing would be stricter and would contradict a decision the boundary
already froze, so the frozen sentence is implemented, the quote sits beside
the code and in the case, and the disagreement is on the handoff rather than
buried.

### Four findings, one correction

Shape and seal bypassed; the deciding policy fact discarded; the act neither
replay- nor collision-safe; the first answer aliasing the caller's object.
They converge: build the complete frozen `turnRecord`, validate before reading
semantic members, seal it, and commit through the operation journal — whose
byte-stable result is the answer. Schema 10 → 11 adds the canonical body, its
seal and a `policy_failures` column, so the evidence that selected an outcome
sits beside the outcome.

### Two mutations measured rather than counted

E4 is **masked**: the record-level validation covers policy failures too, so
removing only the per-failure check leaves the malformed case caught. Both
must go. The per-failure check is kept because its refusal names *which*
failure, and it is not counted as a guard.

E6 is **equivalent**, and the reason is the correction itself: `store.transact`
returns the byte-stable JSON it committed, so the answer is already owned. The
journal is what makes it owned, not the clone, and the comment says so.

### Verification

- `cd v12 && npm test` — **487 pass, 0 fail**; zero test-owned roots retained.
- Eight mutations, six witnessed and two measured.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Event normalization, the adapter contracts and the
re-identification gate remain.

## The turn slice, second correction — 2026-08-23

`review-2026-08-23T03-32-55Z.md`, two P1. Reproduced before any edit — 489
tests, 487 passed, the two additive regressions the only failures. Both
correct. Evidence: `evidence/correction-agent-turn-round2-2026-08-23.txt`.

### The disagreement, resolved

The re-review supersedes its own prior point: §10.6 does say an unrecognized
`codexErrorInfo` takes the final row, and the implemented answer is the
recorded contract. Raising it on the handoff rather than diverging silently
was the right shape — and worth noting, the divergence I was asked for would
have been the **stricter** one. Being stricter than a frozen contract is still
disagreeing with it.

### A scan over a projection is a scan over the projection

The operation journal scans the result it commits, and that summary omits
`evidence` and `adapter_diagnostics` — exactly where a bearer would sit. So a
live bearer under an innocently named diagnostic landed in `turns.body` while
the journal committed a clean summary and reported no leak. I had reasoned
that the journal's durable-secret boundary covered this; it covers what it is
*given*.

### A seal the consumer does not consult protects nobody

I added a sealed canonical record and then left the one safety decision
reading `turns.permitted` directly. The gate consumes the sealed record now,
and the summary must **agree** with it: a drifted query column is an integrity
failure wherever it is found, because the next reader may be one that only has
the column.

`turnRecordOf` also binds a fourth witness — the identity the caller asked
for. Three digests can agree while the record answers to somebody else's turn,
which is what copying one row's body and seal onto another produces.

### Two mutations measured rather than counted

F2 is **masked** by the summary-versus-record comparison; F5's shape check on
read is **inert** given the write-side validation and the seal. Both are kept
— a loader that trusts what it parses is the shape this Work has corrected
twice — and neither is counted as a guard.

### One reviewer assertion scoped

Their bearer case asserts `operations` is empty; the table is not empty and
never was, because the fixture's `recordAttempt` journals before any turn
exists. Scoped to `kind = 'agent.turn'`, which is the claim being made, with
the reason beside it.

### Verification

- `cd v12 && npm test` — **492 pass, 0 fail**; zero test-owned roots retained.
- Five mutations, three witnessed and two measured.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2976 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 316/316;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Event normalization, the adapter contracts and the
re-identification gate remain.

## The turn slice, third correction — 2026-08-23

`review-2026-08-23T14-47-38Z.md`, three P1 and one P2. Reproduced before any
edit — 498 tests, 492 passed, the six additive regressions the only failures,
each failing for the exact reason reported. All four findings are correct and
none of them is disputed. Evidence:
`evidence/correction-agent-turn-round3-2026-08-23.txt`.

### Equal bytes are not the same act

I derived the turn identity from the epoch and the prompt digest and called it
"the ONE turn identity". It was one identity for two turns: an epoch may run
more than one supervised turn, and a second one re-sending the same prompt
reached the first turn's operation id and refused. The store could not
represent both.

The component that separates them had to be manager-owned and free of prompt
content, and the contract already named one I had not used — §5.1's
manager-owned deadline. `(started_at, deadline_at)` is the supervision window
that deadline bounds: the manager's own, stable across retry because a retry
replays the window it was given, and carrying nothing the caller authored.

`ended_at` stays OUT of it, and that is the part worth stating. The window is
what the manager ALLOCATED; the end instant is what it later OBSERVED. Folding
an observation into an identity would have quietly minted a second turn
document for a retry that merely reported a different end. Under one window a
changed end keeps the identity and changes the signature, so it collides —
which is the honest answer to "the same turn, described differently", and it
has its own case.

### What I did NOT add, and why

The review said to allocate or validate the component atomically within the
epoch. I validate it; I did not add a uniqueness or serialization rule to the
window itself. An already-accepted case records two turns that share one
window and differ by prompt, and §5 does not say turns in an epoch cannot
overlap. Making the window unique would have refused a case the reviewer
already signed off on the strength of a rule I would have been inventing. The
window is a COMPONENT, the prompt digest still separates that pair, and the
reasoning sits beside the function rather than only here.

### A row existing is not the session it names

I selected `state` and then used the row only for presence. The column was
right there. A `closed` epoch — which §3.3 reaches only once every turn it
started has a terminal fact — accepted a new turn and sealed it, and a caller
naming `provider-session-b` was sealed as accepted evidence against a row
naming `provider-session-a`.

The admitting states are a closed set named POSITIVELY. Listing the states
where a turn may not settle is a list a newly frozen state joins silently and
wrongly; listing where it may means a new state fails the case instead. It is
driven exhaustively off the placed schema's own `sessionState` enum, in both
directions, so the partition cannot drift from the vocabulary it partitions.

### One immutable answer, then everything that moves

Both the durable-secret scan and that admission ran before the journal could
answer, and both read state that MOVES. That is one shape, not two bugs: an
exact retry of an already committed turn was being decided by an ephemeral
registry and a mutable session row, neither of which existed in that form when
the answer was committed. Moving both inside `store.transact`'s action puts
the journal first — replay replays, a changed operand collides, and a
genuinely new write still refuses on both counts.

### One deliberate strictness, raised not buried

The review asked that a terminal or ambiguous epoch admit no new turn. I also
refuse `not-started` and `initializing`, because no prompt has been issued in
either and a turn cannot have settled. That is more than was asked, and
nothing in this slice moves a session out of `not-started` yet — so a later
slice's state transitions must reach an admitting state before recording a
turn. If the reviewer wants that narrowed to the two terminal states, it is one
line and I will change it.

### One mutation measured rather than counted

M7 is **masked**: removing `turnSessionRef` leaves every malformed-reference
case still refusing with the same closed pair, because the reference is a
member of the frozen `turnRecord` and the record-level validation rejects it.
It is kept because the reference now reaches the identity digest and the
durable body before any row is read, and its case asserts the BEHAVIOUR — that
no caller-supplied shape escapes the closed taxonomy — rather than that line.
It is not counted as a guard.

### Verification

- `cd v12 && npm test` — **504 pass, 0 fail**; zero test-owned roots retained
  under a TMPDIR bracket.
- Eight mutations, seven witnessed and one measured.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2977 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was edited or weakened; the six additive cases are
new.

### State

**Awaiting re-review.** Event normalization, the runtime/agent adapter
contracts and the re-identification gate after transport ambiguity remain.

## The turn slice, fourth correction — 2026-08-23

`review-2026-08-23T15-09-47Z.md`, one structural P1 and one P2 with two parts.
Reproduced before any edit — 506 tests, 504 passed, the two additive
regressions the only failures, each for the exact reason reported. Evidence:
`evidence/correction-agent-turn-round4-2026-08-23.txt`.

### I restated the requirement instead of meeting it

The third review asked for one stable manager-owned identity per supervised
turn, ALLOCATED OR VALIDATED ATOMICALLY within the session epoch. I answered
with a digest of the caller's `startedAt` and `deadlineAt`, kept
`promptDigest` in the identity to tell two reuses apart, and wrote a paragraph
explaining why the window counted as manager-owned.

Every clause of the original finding still applied to that answer. Nothing
allocated the window. Nothing recorded that it had been allocated. No
constraint made it unique in the epoch. And prompt bytes were still the
fallback deciding whether one supervised act was one turn or two — which is
the sentence the finding opens with. I even added a case PROVING the window
could be reused when the prompt differed, and argued in the handoff that
refusing that would be inventing a serialization. What I was actually
defending was the absence of an allocation, using a fixture as the evidence
that none was needed. The review's phrase for that — "treating test setup as a
product ruling" — is exact.

### What an allocated identity looks like

§5.1 already says the manager opens a turn and gives it a deadline before
issuing the prompt. That is the one moment at which a turn identity can exist
without deriving from anything the agent said, so that is where it belongs.

Schema 11 -> 12 adds `turn_allocations`. `allocateTurn` claims the next
per-epoch ordinal under `BEGIN IMMEDIATE` and derives the token from
`(attempt, posture, epoch, ordinal)` — nothing else. The UNIQUE constraint is
what makes epoch-local uniqueness a fact rather than an intention, for the
reason the one-open-session-per-posture index already carries: two managers
racing on separate connections both pass any read, and only the database can
refuse the second. `turns.turn_id` REFERENCES the allocation, and `recordTurn`
binds the token to this epoch inside the write transaction.

Prompt bytes went where the review put them. The signature covers the sealed
document, which covers `prompt_digest`, so a changed prompt under one
allocated turn is changed operands for one act and COLLIDES. It can no longer
become a quiet second turn, which is what it silently did while the identity
was carrying it. And the deliberate exclusion of the observed `endedAt` is now
structural rather than argued: no operand reaches the identity at all.

### Two choices I made that the review did not dictate

**Allocation is not journalled.** An operation journal replays an act by its
identity, and allocating is how an identity comes to exist; keying it under an
invented id would be inventing the thing allocation produces. A retried
allocation mints a fresh ordinal and the abandoned one is a gap — visible,
harmless, and honest about a turn the relay opened and did not finish. What
must survive a retry is the RECORD, and it does.

**Allocation does not ask the settle-admitting question.** Opening a turn asks
whether the epoch exists; whether a turn may still SETTLE there is a question
about the moment it settles. Checking state at allocation would also have
pre-empted the record-time boundaries the third review installed, so several
of its own cases would have started passing for the wrong reason.

Both are raised on the handoff.

### Four existing cases touched, all four named

Two ASSERTIONS changed, because the ruling superseded them:
`"the turn identity is derived from its epoch and prompt"` asserted that the
prompt was part of the identity — exactly what this review ruled out — and
`"the manager's supervision window identifies the turn"` was my own third-round
case for the superseded design. Two fixtures had their SETUP revalidated with
assertions untouched: the same-window/different-prompt case the review named,
and the four-outcome case that told four turns apart by prompt bytes. And the
schema pin moved 11 -> 12 as every prior schema round did.

### Nine mutations, and three measurements

Five witnessed individually, one only as a PAIR, two masked. The two clone
guards mutually mask — either alone refuses the reviewer's function element,
and both must go for the case to fail — so neither is counted alone and both
are kept, one for naming what the value was and one for an interior no clone
can own.

The token shape proof is masked, and this time I measured the masking source
rather than asserting it: without the proof, `undefined` refuses in
`canonicalBytes` and null/`""`/`7` refuse in the frozen record validation on
`/turn_id`. Same closed pair, worse message. The
`turns -> turn_allocations` foreign key is masked by the binding that refuses
an unallocated or foreign token first; both are kept, because a key says a
record belongs to an allocation and the binding says WHICH epoch.

The foreign-allocation case needed a second attempt to be worth anything. My
first version closed the execution epoch to make room for a second one, so
admission refused before the binding was consulted and the mutation showed
zero witnesses. Using the CONSENT posture instead keeps the execution epoch
`ready`, so the refusal has to come from the binding — and it does.

### Verification

- `cd v12 && npm test` — **508 pass, 0 fail**; zero test-owned roots retained
  under a TMPDIR bracket.
- Nine mutations: five witnessed, one witnessed as a pair, two measured.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** Event normalization, the runtime/agent adapter
contracts and the re-identification gate after transport ambiguity remain.

## The turn slice, fifth correction — 2026-08-23

`review-2026-08-23T16-15-49Z.md`, one P1. Reproduced before any edit — 509
tests, 508 passed, the additive regression the only failure, at the first
state it drives. Evidence:
`evidence/correction-agent-turn-round5-2026-08-23.txt`.

### I argued against this last round, and the argument was wrong twice

Round 4's record says allocation deliberately skips the state and provider
checks because "opening a turn asks whether the epoch exists; whether a turn
may still SETTLE there is a question about the moment it settles", and adds
that checking at allocation would pre-empt the record-time boundaries the
third review installed.

The distinction is real. The conclusion is backwards. §7.3 draws exactly one
edge that starts a prompt, `ready -> prompting`, so opening asks the STRICTER
question — every other state is either before a prompt is possible or past
one. And §3.3's `closed` asserts that a terminal fact was observed for every
turn the epoch started, so an allocation landing afterwards is not the
harmless gap I described; it makes a durable session assertion false the
instant the row commits. The timing seals it: allocation precedes the external
prompt and recording follows the terminal fact, so a check deferred to
recording is a check made after the thing it exists to prevent.

The second half of the argument was worse. "Checking at allocation would
pre-empt the record-time boundaries, so several of the third review's cases
would start passing for the wrong reason" is a true statement about my
FIXTURES presented as a statement about the design. That is the same move as
round 4's window defence — reasoning from what the tests happened to be built
on — one round after being told about it. The review supplied the migration in
one sentence: open while ready, then move the state, which is what a relay
does.

### The change

`TURN_STARTING_SESSION_STATES` is `["ready"]`, named positively the way the
settle set already was. `admitTurnStart` checks it and binds the full durable
provider reference, inside `allocateTurn`'s existing `BEGIN IMMEDIATE` and
before the insert, so a refused opening leaves nothing behind and the state
cannot move between the check and the row. `admitTurnSettlement` keeps the
separate SETTLE set. The provider comparison is factored into one
`bindProviderSession`, so the two boundaries cannot drift apart on that half
while staying deliberately different on the state half.

### What the migration cost, named rather than glossed

Two of my cases now open while ready and then perturb — the exhaustive
settlement case, which allocates one turn per state up front, and the
omitted-provider case, which opens before the label is attached. A fixture
helper `openTurn` makes the intent explicit.

Two of the reviewer's own round-3 cases — "a closed session accepts no later
turn" and "a turn binds the stored provider session identity" — are now
decided at the START boundary rather than the settle one. Their assertions
hold and I did not touch them, but the boundary they were written for moved
underneath them, and that is worth saying out loud rather than letting a green
run imply otherwise. The settle-side coverage they used to carry is now
carried by the two migrated cases, and I checked that rather than assuming it:
mutations S1 and S2 disable the settle state check and the settle provider
binding, and each still fails a different case.

### Five mutations, all witnessed

Three on the new start boundary (state, provider, and removing it entirely)
and two on the settle boundary, which is the evidence for the paragraph above.

### Verification

- `cd v12 && npm test` — **511 pass, 0 fail**; zero test-owned roots retained
  under a TMPDIR bracket.
- Five mutations, all witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed this round.

### State

**Awaiting re-review.** Event normalization, the runtime/agent adapter
contracts and the re-identification gate after transport ambiguity remain.

## The event-normalization slice — 2026-08-23

First delivery of frozen §6, so there is no review to answer. Evidence:
`evidence/event-normalization-slice-2026-08-23.txt`.

### What I scoped in, and what I left out on purpose

§6.1 through §6.4: the closed ten-kind set, the thirteen-row ACP mapping,
content restrictions, and sealing with sequence, duplicate, lateness and
identity rules.

§6.5's flow control is OUT and it is named here rather than left for a
reviewer to discover. The bounded queue with pinned depth, byte caps and
backpressure is a RELAY structure, not a manager one, and it belongs with the
runtime/agent adapter contracts that are still open. The manager's durable
half of §6.5 already exists and has since the turn slice:
`turns.dropped_event_count` and `dropped_event_bytes` carry the counted
overflow totals.

Session-state gating is also OUT, deliberately. §6.4 gives this boundary
identity, sequence and lateness rules and no state rule. After the last two
rounds I was tempted to add one anyway — but inventing a gate the frozen
section does not state would be this module deciding a question §7.3 owns,
which is the opposite lesson. A case records the omission as a decision so it
reads as a choice rather than a gap.

### The three sentences the design turns on

**Counted, never guessed at.** An update kind this contract has never seen
becomes `other`, keeps the provider's own string, and carries no portable
content — and its bytes are still counted. The two alternatives are inventing
agent evidence and reporting a partial stream as complete.

**`other` carrying no content is a rule, not a description.** This is the one
I nearly got wrong. `user_message_chunk` maps to `other` and arrives WITH
content, so passing content through "when it is there" would have made the
relay's own prompt into durable agent evidence. The mapping table is where
that shows up, and only if you read §6.1 as a constraint rather than a
summary.

**The seal covers the frame, not the observing of it.** `late` and
`observation_seq` are columns beside the document. A retransmitted frame is
the same frame; sealing lateness in would give one frame seen twice two
digests and make an ordinary duplicate look like a spliced stream.

### Thirteen mutations, all witnessed

E9 is the one worth naming: it makes a replay recompute lateness from today's
state instead of replaying what was recorded — precisely the failure §6.4
spends a paragraph forbidding — and a case catches it. E2 catches the
`other`-content rule above from two directions.

### Verification

- `cd v12 && npm test` — **540 pass, 0 fail** (511 before; 29 new cases);
  zero test-owned roots retained under a TMPDIR bracket.
- Thirteen mutations, all witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed; the schema pin moved 12 → 13 with
`agent_events` added to the table list, as every prior schema round did.

### State

**Awaiting first review of this slice.** §6.5's relay queue, adapter prompt
composition, the runtime/agent adapter contracts and re-identification after
transport ambiguity remain.

## The event slice, first correction — 2026-08-23

`review-2026-08-23T16-47-06Z.md`, four P1. Reproduced before any edit — 546
tests, 540 passed, the six additive regressions the only failures. All four
findings are correct and I dispute none. Evidence:
`evidence/correction-event-normalization-2026-08-23.txt`.

### A mapping table is half the contract

I built the tool-call path against `update.toolCall.toolCallId`. The frozen
captured trace carries `toolCallId` and `status` at the update ROOT, so the
normalizer refused the exact provider shape it exists to normalize — and my
own fixture agreed with my code because I wrote both. I read §6.2's table and
never checked it against `evidence/traces.json`, which is the other half of
the same contract and was sitting in the record I was implementing from.

The reasoning defect has the same cause. §6.2 marks `agent_thought_chunk`
content "diagnostics; never portable evidence" — the same sentence about a
different row as the one I did honour for `other` — and I applied it to one
and not the other. A chain of thought in an event's portable `content` is
precisely the durable agent evidence that row forbids.

### An index is not a record

The replay path compared the indexed digest column and answered with metadata
without ever reading the body, so a retained frame that had become unreadable
was reported as a successful replay. The place a stale index is most
convincing is the place a record is never read. `authenticateRetained` is now
shared by the reader and the replay path, and both answers carry the document
§6.4 asks for.

Worth noting against my own last two rounds: I had already learned this exact
lesson for turns — "a seal the consumer does not consult protects nobody" is
in this file — and then wrote a duplicate path that consulted a column.

### An authenticated identity member cannot be optional

A separate `turnId` operand defaulted to null, the sealed `turn_id` was checked
only when the operand happened to be non-null, and the OPERAND was what got
written. A frame sealed for a turn became a durable unbound event whenever a
caller omitted the option. The sealed value is the identity now; a redundant
operand may only agree, and all three disagreement directions refuse.

### A bound over a self-described size is not a bound

I compared `byte_count`, which is source accounting living inside the
untrusted sealed document — a frame may claim `1` while the event is far over
the limit. The bound measures the canonical bytes of the thing being bounded
now. `byte_count` keeps its distinct job, and a case of mine drives the
converse the review's does not: an enormous claimed source count with a small
canonical event is admitted and the count survives unrewritten.

### Three migrations, each with its authority named

Two fixtures moved to the captured root-level tool-call shape with every id
and status assertion preserved, and one exact expected answer was extended
with the document §6.4 requires. All three are authorized case-specifically in
the review, and each carries a comment saying so beside it.

### One thing I am carrying forward rather than resolving

§6.2's prose says `tool_call` carries the ACP `kind`; the frozen
`$defs.toolCallView` permits only `tool_call_id`, optional `title` and
`status` with `additionalProperties: false`. Two frozen artefacts disagree.
The review says not to invent the member and I have not; a case asserts the
normalized view has exactly `tool_call_id` and `status` even when the update
carries `kind`. **It needs an owning record before anything relies on that
field**, and I have raised it on the handoff rather than filing one myself,
since formal enrichment and priority are the reviewer's and Slawomir's.

### Nine mutations, eight witnessed

C4 is measured rather than counted: the answer's clone is EQUIVALENT, because
`authenticateEvent` already reaches an owned object through a serialize/parse
round-trip. That round-trip is what makes the answer owned, not the clone. It
is kept and not counted as a guard.

### Verification

- `cd v12 && npm test` — **550 pass, 0 fail** (540 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Nine mutations, eight witnessed and one measured.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

### State

**Awaiting re-review.** §6.5's relay queue, adapter prompt composition, the
runtime/agent adapter contracts and re-identification after transport
ambiguity remain.

## The event slice, second correction — 2026-08-23

`review-2026-08-23T17-01-19Z.md`, one P1 and one P2. Reproduced before any
edit — 552 tests, 550 passed, the two additive regressions the only failures.
Both findings are correct. Evidence:
`evidence/correction-event-normalization-round2-2026-08-23.txt`.

### Binding three quarters of a reference is not binding it

`eventRecordOf` takes the full session reference, selected its row on attempt,
posture and epoch, and then authenticated only the seal and the sequence. So a
caller asking for provider session B was handed a frame sealed for provider
session A — the same identity mismatch the WRITE path already refuses,
reachable by asking instead of by writing. I had written that write-path check
myself two rounds ago and did not carry it to the reader.

The requested reference is a fifth witness now. And absence and disagreement
are deliberately different answers: an absent `(attempt, posture, epoch,
source_seq)` is null, while a present row whose sealed reference disagrees
refuses — answering null there would tell a caller no such frame exists while
the epoch holds one, which is a worse lie than the one being fixed.

### An interpreter exception is not a closed pair, at a third boundary

This is the same rule the turn slice learned twice, now found in `sealEvent`.
`structuredClone` ran over content, tool-call data and diagnostics before the
schema boundary. All three go through `ownDurable`, and the seal is wrapped
separately because `canonicalBytes` is the other place a caller's value
becomes durable — and a precise existing `ContractError` passes through
unchanged, because a general "cannot own this" would report the same pair
while telling the caller less.

### Two of my own mutation instruments were wrong, and both were silent

Worth recording plainly, because I have been reporting mutation counts as
evidence for several rounds.

The first read `if (false && a || b || c || d)`. `&&` binds tighter than `||`,
so it disabled only the first clause — a differing attempt id, which no case
drives because that makes the row absent rather than mismatched. It reported
zero witnesses and meant nothing.

The second was an assertion, not a mutation: my precise-refusal case required
only that `/infinity/` appear in the message. Flattening INTERPOLATES the
precise text into the general refusal, so the pattern still matched and the
mutation reported zero. The case now also requires the general wrapper to be
absent.

A mutation that reports zero is a claim about the code. Twice here it was a
defect in the instrument instead, which is the same class of error as trusting
a fixture I wrote myself — the thing the first event review caught me doing.
Both are fixed and both now fail.

### Two measurements

The retained-reference comparison is INERT from the replay path, because equal
digests already mean equal references there; it is one function because the
rule is one rule, and the reader is where it has teeth. `ownDurable`'s
ContractError pass-through is UNREACHABLE, because `structuredClone` raises no
`ContractError`; it is kept for symmetry with the seal wrapper, where the same
line is load-bearing. Neither is counted as a guard.

### The carried contract defect has an owner

W543 at `work/records/2026/08/finding-acp-tool-call-kind-contract-conflict/`
now owns the §6.2-prose versus `toolCallView` disagreement. This slice
continues to invent no `kind` member and the case recording that omission is
unchanged. Nothing here waits on W543.

### Verification

- `cd v12 && npm test` — **555 pass, 0 fail** (550 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Eight mutations: seven witnessed, one measured as unreachable.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed this round.

### State

**Awaiting re-review.** §6.5's relay queue, adapter prompt composition, the
runtime/agent adapter contracts and re-identification after transport
ambiguity remain.

## The handshake slice — 2026-08-23

Item 4q was signed off, so this is the next serial slice: frozen §2.1-§2.5,
the handshake and the closed surface. First delivery, no review to answer.
Evidence: `evidence/handshake-slice-2026-08-23.txt`.

### What I scoped in, and the five exclusions

IN: version negotiation and provider certification, the withheld client
surface, the required/optional/refused method sets, the six Baton
agent-session capabilities, and experimental surfaces as diagnostics.

OUT, named here rather than left for a reviewer to find: §8.1 identity
preservation and §8.2 the relay journal, which are about what the relay sends
and records frame by frame and need the transport; §8.4 reconnect ambiguity,
already named as still-open and reaching into W151's ambiguity path; §8.5
cancellation forwarding, whose manager half is already signed off in items
3l-3o and whose forwarding half is a relay act; and §6.5's queue, unchanged
from the event slice's statement.

### The three sentences it turns on

**The sets belong to the version, not to a profile.** §2.3 says so and gives
the reason — a certified profile that disagrees with the enforced policy is a
second source of truth wearing the first one's authority. So they are module
constants and the profile supplies only which wire, which version, which
build.

**The relay advertises nothing, and the comparison is exact.** A subset check
asks whether what is present is safe; the rule is that nothing may be present.
`session` is stable, is not in the unstable set, and is still not advertised —
that is the difference between the two readings, so a case asserts it.

**Binding replaces negotiation.** A provider with no protocol version has
nothing to negotiate against, so certification binds an exact build and
interface digest instead, and each door refuses the other's profile.

### I tested against the frozen model, not against my own transcription

The first event review caught me building from §6.2's prose while the captured
trace said otherwise, with a fixture that agreed because I wrote both. So the
case file PARSES `evidence/acp_boundary_model.py` and compares the four sets
member for member. A set I transcribe twice is a set I can get wrong twice in
the same direction, and comparing my copy against my other copy would not have
found it.

### One instrument was at fault again, and I caught it this time

The wire-protocol mutation reported zero witnesses. Last round's evidence
records that class of error twice, so I checked instead of believing it: the
case offered wire version 1 against a profile pinning null, so the VERSION
rule refused first with the same pair for a different reason and the rule
being named was never consulted. Offering the pinned null makes only that door
able to refuse, and the mutation fails.

One genuine measurement: the experimental-API check is UNREACHABLE for a
certified profile, because the frozen schema makes `experimental_api` a
constant `false`. The case drives the refusal at certification, which is where
it lands. The check is kept so a reader sees the rule where the binding is
read, and it is not counted as a guard.

### Verification

- `cd v12 && npm test` — **569 pass, 0 fail** (555 before; 14 new cases);
  zero test-owned roots retained under a TMPDIR bracket.
- Thirteen mutations: twelve witnessed, one measured as unreachable.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed; no schema change was needed.

### State

**Awaiting first review of this slice.** §§6.5, 8.1, 8.2, 8.4 and 8.5, adapter
prompt composition, the runtime adapter contract and transport-ambiguity
re-identification remain. W543 owns the tool-call `kind` conflict and is
untouched.

## The handshake slice, first correction — 2026-08-23

`review-2026-08-23T17-26-19Z.md`, two P1. Reproduced before any edit — 573
tests, 569 passed, the four additive regressions the only failures. Both
findings are correct. Evidence:
`evidence/correction-handshake-2026-08-23.txt`.

### I claimed a closed surface and built two deny lists

This one deserves stating plainly, because the slice's own header comment
claimed the opposite and I wrote the handoff message saying so.

`checkOutboundMethod` rejected the twenty-one names §2.3 enumerates and
returned every other string, so `session/reuse` — the frozen contract's own
example of a capability that does not exist — passed, and so would any method
a future SDK adds, on the day it adds it. `serveClientMethod` had the same
shape over ACP 1.3.0's eight client methods.

§2.2 says withholding by default costs nothing while "advertising by default
means every future SDK release silently widens the boundary". I quoted that
sentence in the module header and then implemented the widening it describes,
twice. The enumerated lists made the guards LOOK closed and the exhaustive
cases over those lists made them look tested; what neither showed was the
default.

Both are allow lists now. The outbound surface admits only the eight methods
that exist in 1.0, and whether an OPTIONAL one may be used on a given session
depends on its advertisement and the pinned policy — neither of which is in
hand here, so that check is named as composition's rather than silently
skipped. The client surface denies EVERY method, because there is nothing to
enumerate when nothing is advertised.

### One function was answering two questions

Which client capabilities are served (none) and which agent-origin calls are
accepted (one) are different questions. `session/update` is the single member
of the required five that flows agent-to-client, so it belongs to the second;
`routeAgentOriginCall` owns it now and the migrated assertion sits there
rather than being dropped.

### One constant for two different documents

§2.2's wire document is `{ "fs": {}, "terminal": false }` with both filesystem
members ABSENT, because the pinned SDK declares them optional. The
agent-session schema separately records a normalized snake-case summary with
both explicitly false. I had one constant for both, so the boundary refused
§2.2's own example and `negotiateAcp` emitted field names ACP does not have.

Two names now, and a case asserts they differ. The comparison is structural
rather than serialized — member order carries no meaning, and a rule that
depends on it is a rule about insertion rather than content. And absence is
how the wire withholds: an `fs` member present at all, even set `false`, is
denied.

### Four migrations, each with its authority named

The withholding case now names the wire document and additionally asserts the
two representations differ; the exactness case drives the wire shape with the
durable summary added as a denied case; the negotiation case expects the wire
document with its fresh-copy assertion unchanged; and the client-method case
keeps all eight and asserts `session/update` is denied there too, since its
routing assertion moved rather than vanished.

### Eight mutations, all witnessed

W5 and W6 are the ones that matter: reverting either guard to exactly what I
delivered last round now fails, including on a method the contract has never
heard of.

### Verification

- `cd v12 && npm test` — **574 pass, 0 fail** (569 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Eight mutations, all witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

W641 owns the frozen-artifact conflation between the model, the schema and
§2.2. This slice follows §2.2's wire text and the pinned SDK declaration as
the review directs, and rewrites neither artifact.

### State

**Awaiting re-review.** §§6.5, 8.1, 8.2, 8.4 and 8.5, adapter prompt
composition, the runtime adapter contract and transport-ambiguity
re-identification remain.

## The handshake slice, second correction — 2026-08-23

`review-2026-08-23T17-39-42Z.md`, one directional P1. Reproduced before any
edit — 575 tests, 574 passed, the additive regression the only failure. The
finding is correct. Evidence:
`evidence/correction-handshake-round2-2026-08-23.txt`.

### My own correction missed the thing it was about

Last round I split the inbound route out of the client-call boundary and wrote
that "direction answers two different questions". Then I built the outbound
allow list as required-plus-optional — all five plus three — so it still
admitted `session/update` in the reverse direction. The two closed directional
surfaces I had just separated overlapped on the exact name the separation was
about.

The mistake is a misreading of §2.3: its five-member baseline says what an
ENDPOINT must present across both directions, and I used it as a
relay-outbound list.

### Revalidated against the pinned SDK, not the prose

That is now twice in this slice, so I went to the artefact.
`@agentclientprotocol/sdk` 1.3.0's `dist/schema/index.js` puts `session_update`
in `CLIENT_METHODS` alongside the `fs/*`, `terminal/*`, `mcp/*` and
`elicitation/*` names, and puts `initialize`, `session/new`, `session/prompt`,
`session/cancel` and all three optional methods in `AGENT_METHODS`. Four plus
three.

### Derived rather than transcribed

`RELAY_OUTBOUND_SURFACE` — renamed on the review's authority so the direction
is in the name — is the required baseline MINUS what the agent originates,
plus the optional three. Deriving it means the two directional lists cannot
drift apart under a later edit to either, which is the failure I just made by
hand.

### Partition, not merely disjoint

The reviewer asked for disjointness. I added coverage as well: between them
the two surfaces account for every required name, and no agent-origin name may
appear that is not part of the baseline. Disjointness alone would let a
required member be dropped from both lists unnoticed — and one of my mutations
(emptying `AGENT_ORIGIN_METHODS`, which silently reproduces the old
eight-member list) is caught by the coverage half rather than the disjointness
half.

### Verification

- `cd v12 && npm test` — **576 pass, 0 fail** (574 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Four mutations, all witnessed, including one that reproduces exactly what I
  delivered last round.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

One existing assertion migrated on the review's explicit authority, with the
five-member handshake requirement and the three optional members preserved by
name, and one rename inside the reviewer's own case.

### State

**Awaiting re-review.** §§6.5, 8.1, 8.2, 8.4 and 8.5, adapter prompt
composition, the runtime adapter contract and transport-ambiguity
re-identification remain. W543 and W641 own their contract defects.

## The session-axis slice — 2026-08-23

Item 4u was signed off, so this is the next serial slice: frozen §7.3-§7.4,
the agent-session observation axis. First delivery, no review to answer.
Evidence: `evidence/session-axis-slice-2026-08-23.txt`.

### I picked this because my own record said it was missing

The turn slice reads `agent_sessions.state` for its start and settle
admission, and the event slice deliberately does not gate on it. But nothing
WROTE the axis: `openAgentSession` inserts `not-started` and
`closeAgentSession` sets `closed`, so seven of the nine states were
unreachable. The turn slice's progress note said exactly that — "nothing in
this slice moves a session out of not-started yet" — and it was still true
four slices later.

### The design

The nine states and the successor table are transcribed from the frozen model,
and the case file PARSES that model's table and compares edge for edge. §7.3's
diagram draws the spine; the model carries the edges the spine does not draw,
including `turn-ended -> prompting` for a second supervised turn in one epoch
— the fact the turn slice's allocated identity exists for.

A self-observation is a no-op ANSWER rather than a refusal, because observing
the same state twice is ordinary and refusing it would make a duplicate look
like a regression. The move is decided inside the write transaction, for the
reason the runtime observations already carry.

All eighty-one ordered pairs are driven in both directions, with the permitted
count derived from the table rather than counted by the loop.

### The edge I got wrong first

My initial case asserted that every non-terminal state can reach `unknown`.
`agent-quiescent` cannot, and the frozen table is right: it means a terminal
turn fact WAS observed after cancellation was ordered, so the ending is known,
and `unknown` there would be a regression in knowledge rather than the honest
absence of it. The case states the exception explicitly now.

### A conflict with signed-off code, filed rather than fixed

`closeAgentSession` sets `state = 'closed'` for any row not already closed.
Four of those edges are forbidden by the frozen table — `not-started`,
`prompting`, `cancel-requested`, and `unknown`, which §3.3 names by name as
recording knowledge that was never acquired. I measured it rather than
asserting it; the probe and its output are retained in `evidence/`.

I did not rewire it, for two reasons. Existing signed-off cases close freshly
opened sessions to free the posture, so routing close through the axis would
fail them — and editing signed-off assertions to match my new module is the
move I have been corrected for twice. And underneath there is a contract
question that is not mine: the partial unique index frees a posture only at
`closed`, while the frozen table lets a never-initialized session end only at
`unknown`, which by deliberate design does not free it. A strict reading
deadlocks the posture. That needs a ruling, not an implementer's choice.

So it is raised for an owning record, the way the tool-call `kind` and
client-capability conflicts were before they became W543 and W641. The new
module papers over nothing: it refuses every forbidden edge.

### A zero-witness mutation that was a claim about my test

Two validations mutually mask. Either alone catches a bad state arriving
against a good stored one, or the reverse — but the input where neither covers
for the other is observing an invented state against a row that already holds
that same invented state, because the self-observation shortcut answers before
anything is proved. My case did not drive it. It does now, and the pair
mutation fails.

That is three rounds running where checking a zero found something. Twice it
was a broken instrument; this time it was missing coverage.

### Verification

- `cd v12 && npm test` — **588 pass, 0 fail** (576 before; 12 new cases);
  zero test-owned roots retained under a TMPDIR bracket.
- Eight mutations: six witnessed, one witnessed only as a pair.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed and no schema change was needed.

### State

**Awaiting first review of this slice**, and the `closeAgentSession` conflict
needs an owner. §§6.5, 8.1, 8.2, 8.4 and 8.5, adapter prompt composition and
the runtime adapter contract remain.

## The session-axis slice, first correction — 2026-08-23

`review-2026-08-23T18-02-11Z.md`, one P1. Reproduced before any edit — 590
tests, 588 passed, the two additive regressions the only failures. The finding
is correct. Evidence: `evidence/correction-session-axis-2026-08-23.txt`.

### The third time, and worth counting

`observeAgentSessionState` built its reference from attempt, posture and epoch
and dropped `providerSessionId`, so a label naming provider session B moved
the row held for A — and a malformed reference reached SQLite as a raw binding
error instead of a closed pair.

§3.1 makes the provider id the fourth component of the reference that labels
evidence. The turn boundary binds it. The event write path binds it. The event
read path did not, and that was corrected two rounds ago in exactly the words
"binding three quarters of a reference is not binding it". Then I wrote a new
module that bound three quarters.

I think I know why it repeats, and it is worth writing down rather than just
apologising for. The missing component authorizes nothing, so its absence
never breaks a happy path: the row is found, the state moves, every ordinary
case passes. And my case file was exhaustive — all eighty-one ordered
transition pairs, in both directions, derived from the frozen table. None of
them was about identity. Exhaustive coverage of the wrong axis reads exactly
like thorough work, which is what made it invisible to me twice in a row.

The practical consequence for the slices still open: every boundary that takes
a session reference gets the identity question asked of it explicitly, not
inferred from whether its own subject-matter cases pass.

### A no-op is still an observation

The review's sharpest point. Affirming that provider session B's axis reads
`prompting` is a claim about B, and answering it from A's row is the same
mistake as moving A's row. So the binding precedes the self-observation
shortcut rather than sitting after it — and one of my mutations keeps the
binding but moves it a single line past that shortcut, which is precisely the
shape a correction that only thought about MOVES would have produced. It
fails.

My two added cases drive that half from both sides: the same-state
observation over all nine states the row can hold, so nothing would move even
if the binding were skipped, and the mirror where the session is unlabelled
and saying something is the disagreement.

### W771

The `closeAgentSession` conflict I raised last round is now durably owned by
W771 at `work/records/2026/08/finding-agent-session-close-axis-conflict/`,
high priority. Nothing here changes the frozen successor table, weakens a
signed-off close assertion or papers over `unknown`. **Final W4 composition
must revalidate W771's disposition**, and this correction does not discharge
it — recorded in PLAN item 4x so it cannot be lost to a progress note.

### Verification

- `cd v12 && npm test` — **592 pass, 0 fail** (588 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Four mutations, all witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed and no schema change was needed.

### State

**Awaiting re-review.** §§6.5, 8.1, 8.2, 8.4 and 8.5, adapter prompt
composition, the runtime adapter contract and transport-ambiguity
re-identification remain, plus W771 at final composition.

## The reconnect slice — 2026-08-23

Item 4x was signed off, so this is the next serial slice: frozen §8.4,
reconnect ambiguity. First delivery, no review to answer. Evidence:
`evidence/reconnect-slice-2026-08-23.txt`.

### Why this one, and the first composition

§8.4 has been on every "still not implemented" list this Work has written, and
the session axis landing last round is what made it buildable — transport loss
is exactly the ordinary way an epoch reaches `unknown`, and until the axis
existed there was no boundary to move it through. This is the first slice that
COMPOSES two earlier ones rather than sitting beside them.

### The design

A lost transport ends the epoch. The durable move goes through
`observeAgentSessionState`, so the full §3.1 reference is proved and bound
exactly as it is everywhere else, and the answer reports the three facts §8.4
names plus the outcome.

The outcome is REPORTED and not recorded. `recordTurn` needs an allocated turn
token, a prompt digest and the supervision window, and this boundary holds
none of them — inventing them to write a turn document would be minting
evidence about a turn it never saw. A case asserts `transport-lost` is one of
the closed eight, so this cannot become a second outcome vocabulary.

Whether a turn was in flight is STATED, not inferred. It decides an outcome,
and §5.4 spends a section on what an outcome may not be derived from, so a
non-boolean refuses rather than being read as truthy.

Re-prompting is `ambiguous.operation` and not `refused.precondition`: the
manager is not saying the request is malformed, it is saying it cannot KNOW
what the first attempt did. The prompt argument is ignored on purpose.

### What I did not build, said rather than omitted

W151 §9's positive re-identification gate is another Work's and needs runtime
inspection this slice does not have. But the FLAG is implemented:
`nextEpochAllowedWithoutRuntimeReidentification: false` is an explicit answer
rather than an absence, so a later slice that mints an epoch contends with a
recorded `false` instead of a gap in a section it may not have read.
`nextEpoch` is untouched and this slice adds no gate to it — named so the
boundary is not mistaken for one.

### The identity commitment, kept

The last correction ended on a commitment: every boundary taking a session
reference gets the identity question asked of it explicitly rather than
inferred from whether its own subject-matter cases pass. That finding needed
three rounds because the missing component never breaks a happy path. So this
slice has an identity case from the start — wrong label, four malformed
references, and the agreeing case — written before the subject-matter cases
rather than after a review.

### Verification

- `cd v12 && npm test` — **601 pass, 0 fail** (592 before; 9 new cases); zero
  test-owned roots retained under a TMPDIR bracket.
- Eight mutations, all witnessed. R2 is the one §3.3 exists to prevent —
  ending the epoch at `closed` rather than `unknown` — and it fails both at
  the axis and in the answer.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed and no schema change was needed.

### State

**Awaiting first review of this slice.** §§6.5, 8.1, 8.2 and 8.5, adapter
prompt composition, the runtime adapter contract and W151 §9's
re-identification gate remain. W771 stays mandatory to revalidate at final W4
composition.

## The reconnect slice, first correction — 2026-08-23

`review-2026-08-23T18-21-55Z.md`, two P1. Reproduced before any edit — 603
tests, 601 passed, the two additive regressions the only failures. Both
findings are correct. Evidence:
`evidence/correction-reconnect-2026-08-23.txt`.

### Two reads of one untrusted value

The axis validated and bound its own normalized copy of the reference; the
answer then spread the CALLER's object again and read `providerSessionId` a
second time. So a getter could answer provider A to the check that committed
the epoch and provider B to the record of it, and members the closed §3.1
shape does not have rode along into something that looks like a session
reference.

`store.mjs` in this same tree already carries the lesson, written by me
several slices ago: "a `toJSON` method can return `{diagnostic: <bearer>}`
while `Object.entries` shows only the method". One read to decide and a second
to report is that shape exactly, and I wrote it again at a new boundary.

`normalizeAgentSessionRef` is exported from the axis now, the reference is
proved once, and the same object goes to the axis and into the answer. The
proof also moved BEFORE the durable observation — one of my mutations keeps
every check and only moves it a line after the commit, which is the shape a
correction that thought about validation but not about order would produce.

### A default is for an argument nobody gave

`{ turnInFlight = false } = {}` defaults only for `undefined`, so an explicit
`null` reached a property read and left as a raw `TypeError`, while a boolean,
string or array destructured to `undefined`, took the `false` default, and
committed the epoch on operands nobody proved.

**And my first fix made the same mistake one level down.** I wrote
`options?.turnInFlight ?? false`, which turns an explicit `null` MEMBER into
the default. The case I had already written for this slice — that whether a
turn was in flight is stated rather than inferred — failed immediately and
caught it. That is the value of writing the refusal case before the
convenience: it was there to catch me.

### Verification

- `cd v12 && npm test` — **605 pass, 0 fail** (601 before); zero test-owned
  roots retained under a TMPDIR bracket.
- Six mutations: five witnessed, one measured as equivalent.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green.**

No existing test assertion was changed and no schema change was needed. The
axis module gained one export and changed no behaviour; its signed-off 16-case
suite is unchanged and green.

### State

**Awaiting re-review.** The next-epoch flag remains reported rather than
durable enforcement. §§6.5, 8.1, 8.2 and 8.5, adapter prompt composition, the
runtime adapter contract and W151 §9's gate remain; W771 stays mandatory at
final W4 composition.

## The reconnect slice, second correction — 2026-08-23

`review-2026-08-23T18-32-05Z.md`, one P1. Reproduced before any edit — 14
tests, 13 passed, the additive regression the only failure. The finding is
correct. Evidence: `evidence/correction-reconnect-round2-2026-08-23.txt`.

This is the failure W771's handoff named and left standing. It belonged to
W4's open round, so I fixed it here rather than inside W771 — the change
belongs in the record that owns it.

### I wrote the rule and then implemented its opposite

Last round's finding was "a default is for an argument nobody gave, not an
argument somebody gave wrongly". I put that sentence in the code. The check
under it was `typeof options !== "object" || Array.isArray(options)`, which is
true of a Date, a Map, a regular expression and every class instance — each of
which took the absent-member default and committed the epoch from `prompting`
to `unknown`.

The defect the paragraph describes survived the fix aimed at it, because "not
a primitive and not an array" is not "is a record".

**And it is the third allow-rule implemented as a deny-rule in this Work.**
The handshake slice's two method surfaces were the first two, and that
correction is where I wrote that a deny list "silently widens when an SDK adds
a method". A type test that admits everything except two known shapes widens
exactly the same way. I have now made that mistake at a method surface, at a
client surface, and at a type check — which suggests the pattern is not about
methods at all: whenever I write "reject X" I should be asking what the
default answer is for everything that is not X.

### The change

A record is a PROTOTYPE test, because it is the only one that generalizes.
`Object.create(null)` is admitted deliberately — no class, no behaviour, so it
is a document — and a promise, a typed array and a boxed string are refused
for the rule rather than because somebody listed them. The optional member is
read with `hasOwnProperty`. Refusal messages name a value by its constructor,
since a Map and a class instance both stringify to `{}` and a refusal reading
"{} is not an options document" would tell a caller it passed an empty one.

### The reviewer's case corrected mine

I first wrote the ownership case as `Object.create({ turnInFlight: true })`
taking the absent default. The reviewer's own case lists that shape among
those that must REFUSE — and the prototype rule refuses it before ownership is
asked. I changed my case to match the ruling rather than the other way round.

Then the own-member rule had no witness, so I looked for the input that
actually reaches it: a plain record whose `turnInFlight` lives on
`Object.prototype` itself. The case pollutes the prototype, asserts an empty
document takes the honest default, restores it in a `finally`, and separately
asserts an own member still decides. Without it the rule would have been
unwitnessed defence.

### Verification

- `cd v12 && npm test` — **624 pass, 0 fail**; zero test-owned roots retained
  under a TMPDIR bracket.
- Four mutations, all witnessed.
- All four design models green: 64, 56, 74, 24.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

**Every gate in the tree is green**, including the one W771 left standing.

### State

**Awaiting re-review.** The next-epoch flag remains reported rather than
durable enforcement; W151 §9 stays deferred. W771's lifecycle has landed and
is awaiting its own review; its plan item 5 — re-reviewing W4 composition and
every adapter consumer against the corrected lifecycle — remains open and is
not discharged by this correction.

## The reconnect slice, third correction — 2026-08-23

`review-2026-08-23T18-55-02Z.md`, one P2 with two parts. Reproduced before any
edit — 18 tests, 16 passed, the two additive regressions the only failures in
that file. Both findings are correct. Evidence:
`evidence/correction-reconnect-round3-2026-08-23.txt`.

### The code I added to make refusals better became the escape route

`describe()` did not exist before the previous round. I added it so a refusal
would not read "{} is not an options document" when a caller passed a Map. It
called `JSON.stringify`, which throws a raw `TypeError` on a BigInt, and it
read `getPrototypeOf(value).constructor.name`, which an untrusted prototype
may define as a throwing getter.

So at the exact moment the boundary had DECIDED to refuse, it ran the rejected
value's behaviour and lost the decision. That is the same shape as the two P1s
it was written alongside — an operand reaching a boundary that had not proved
it — with the aggravating detail that this operand had already been proved
unacceptable.

**A refusal must never run the value it is refusing.** Diagnostics are where
the temptation lives, because a better message needs to know more about the
value, and knowing more means touching it. The facts are inert now — `typeof`,
`Array.isArray`, a wrapped prototype comparison — and deliberately coarse.

### Two measurements rather than a count

Removing the reflection wrapper ALONE fails no case: `getPrototypeOf` does not
throw on any ordinary JavaScript value, so it is defence against host and
Proxy exotica and is not counted as a guard. Re-adding the constructor read
alone is caught BY that wrapper. What the cases witness is the pair — and the
guard that actually carries the finding is not reading the constructor at all.

Reporting that as "four mutations, four witnessed" would have been true and
misleading.

### My own case asserted an outcome instead of a rule

I wrote the accepted-document case expecting a plain record carrying a
throwing `Symbol.toStringTag` to be REFUSED. Its prototype is
`Object.prototype` and it has no own `turnInFlight`, so the plain-record rule
accepts it and the absent default applies — correctly. I had asserted the
outcome I assumed rather than the rule that applies. The case now asserts the
rule, and that reaching the default ran nothing, which is the better property
anyway: the boundary does not touch a value it ACCEPTS either.

### Verification

- W4's own suites: reconnect **21/21**, axis **16/16**, turn **50/50**,
  handshake **21/21**. The two failures that were W4's last round are fixed.
- `cd v12 && npm test` — 633/640; zero test-owned roots under a TMPDIR
  bracket. **None of the seven remaining failures is W4's**: two are W543's
  first review round on the tool-call `kind` ruling and five are W771's on the
  posture-slot lifecycle. The ACP boundary model's 1 failure and 1 error are
  the same W543 round.
- `pytest -n auto -m "not serial" tests/work` — **2980 passed, 0 failed**;
  `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting re-review.** The next-epoch flag remains reported rather than
durable enforcement; W151 §9 stays deferred; W771's plan item 5 remains open
and is not discharged here.

## The reconnect slice, fourth correction — 2026-08-23

`review-2026-08-23T19-13-23Z.md`, one P2 with two parts. Reproduced before any
edit — 23 tests, 21 passed, the two additive regressions the only failures in
that file. Both findings are correct. Evidence:
`evidence/correction-reconnect-round4-2026-08-23.txt`.

### I wrote the rule, then applied it at one of two sites

Last round I wrote that a refusal must never run the value it is refusing, and
that translating an unavoidable reflection failure is cheaper than proving no
Proxy can make `getPrototypeOf` throw. Then I wrapped the reflection in
`describe` and left the one in `isPlainRecord` bare — and `isPlainRecord` runs
FIRST, so a trapping Proxy leaked past the guard I had just written for it.

There is one translated snapshot now, taken once and shared, so there is a
single place the reflection happens rather than two places that have to agree.

### The part I did not see as reflection at all

`hasOwnProperty` runs nothing, so I read the whole ownership step as inert.
The property read that FOLLOWED it executes an own accessor — so an accepted
plain record could still run the caller's code at a boundary whose entire rule
is that it does not. One guarded own-property descriptor is read now, and only
absence or a data descriptor is an operand.

That is four rounds on one primitive, and each finding has been the same
sentence at a place I had not yet looked: serialize, reflect, read. The
lesson I am taking is that "inert" is a property of a specific operation, not
of a step — `hasOwnProperty` is inert and the line after it was not.

### One measurement, and why it matters here

The accessor refusal is MASKED: an accessor's descriptor has no `value`, so
the boolean proof downstream refuses it with the same pair. What keeps the
getter from running is reading the DESCRIPTOR instead of the property, and
that mutation fails six cases. Reporting five-of-five would have credited the
wrong line.

### Verification

- W4's own suites: reconnect **25/25**, axis **16/16**, turn **50/50**. Last
  round's two failures are fixed.
- `cd v12 && npm test` — 643/649; zero test-owned roots under a TMPDIR
  bracket. **None of the six remaining failures is W4's** — two W543, two
  W641 and two W771 second-review cases, all of which landed while I was
  making this correction, and none touched here.
- `pytest -m serial tests/work` — **52 passed**; codex-event-bridge 336/336;
  acp-baton-bridge 55/55; whitespace clean.

### State

**Awaiting re-review.** The next-epoch flag remains reported rather than
durable enforcement; W151 §9 stays deferred; W771's plan item 5 remains open.

## Fifth reconnect correction — 2026-08-23

`review-2026-08-23T19-42-22Z.md`, one P2 at two edges. Reproduced before any
edit: 25 of 27, exactly the two additive regressions. The finding is correct.
Evidence: `evidence/correction-reconnect-round5-2026-08-23.txt`.

### The comment cleared the operation that was failing

`describe()` has asserted for two rounds that "`typeof` and `Array.isArray`
invoke nothing". True, and not the property that matters — array
classification follows a Proxy to its target, so it throws on a revoked one.
The single classification still outside the translated boundary was the one my
own prose had explicitly exempted, and it leaked a raw `TypeError` on both the
envelope and the member path.

That is four rounds of the same finding on this primitive, and I had been
reading it as a rule about executing CALLER CODE. This operation executes none
and fails anyway. **"Runs no user code" is not "cannot fail"** — every
classification goes through one guarded helper now, so the next one is inside
the translation by construction, and `typeof` is the only exemption left
because it is the only one that cannot throw.

### A catch does not interview what was thrown at it

`ownTurnInFlight` interpolated `failure.message`. A throw carries any value,
so that is a property read on an object the caller chose, and an accessor
there runs the caller's code inside the refusal and replaces the closed pair
with its own Error. No binding, manager-owned text, the same text whatever
was thrown.

### One thing beyond the review, said rather than folded in

With array classification in the snapshot it became visible that
`isPlainRecord` judged documenthood from the prototype ALONE, so a Proxy over
an array wearing `Object.prototype` was a valid options envelope. One line
tests the rule this envelope has always stated instead of inferring it from a
prototype a Proxy is free to lie about.

### Mutations, and one that was a fact about my instrument

Five, all witnessed: array classification back outside the translation (1),
the refusal reading the thrown value (2), an array Proxy accepted as a
document (1), the reflection wrapper removed (5), the descriptor wrapper
removed (3). My first attempt at the first one DID NOT PARSE, which
`node --check` caught before a whole-file failure could look like a witness.

### Verification

- reconnect **29/29**, axis 16/16, turn 50/50, posture slots 25/25.
- `cd v12 && npm test` — **656 tests, 654 pass, 2 fail**; zero test-owned
  roots under a TMPDIR bracket. Both remaining failures are W641's open
  round, in the handshake suite, untouched here.
- design models 64/66/24/74; v11 pytest 2980 and serial 52;
  codex-event-bridge 336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting re-review of item 4ae.** Still unimplemented in W4: the runtime and
agent adapter contracts, composition of the posture lifecycle W771 corrected
(W771 plan item 5), and W151 §9 next-epoch enforcement.

## Sixth reconnect correction — 2026-08-23

`review-2026-08-23T20-09-23Z.md`, one P1. Reproduced before any edit: 29 of 31,
exactly the two additive regressions. Evidence:
`evidence/correction-reconnect-round6-2026-08-23.txt`.

### Five rounds of guards, and the hole was the ordinary case

Every guard I built on this primitive assumed a hostile value MISBEHAVES —
throws from a getter, throws from a trap, will not serialize, revokes itself —
and each round I translated one more failure. A Proxy over `{}` needs none of
that. It answers plausibly, is accepted as an empty options document, and
commits the epoch to `unknown`, having run caller code on the way.

**Translating a trap that throws does nothing about a trap that answers.** That
is the sentence I did not have; all five previous corrections were about the
failure mode I could see happening.

The Proxy test is first and NON-OBSERVING now — `isProxy` reads an internal
slot and runs no trap. Another try/catch would not do, and the review says so:
a successful trap walks straight past one. One guard covers both paths because
both classify through the single helper the fourth correction introduced,
which is the first time that consolidation has paid for itself.

### One assertion of mine superseded, marked where it stood

Last round's dressed-array case asserted the diagnostic "an array" for a
Proxy-dressed array. A Proxy is refused before any reflection now, so it never
reaches array classification and is named for what it is. The two dressed
entries say "a Proxy"; the two bare entries still say "an array"; the refusal
that case owns is unchanged and now happens earlier and without a trap.

### A third instrument slip

Four mutations, all witnessed — but my first attempt at the ordering one
measured zero and was not the mutation I meant: I moved `isProxy` inside the
try while leaving it first, which changes nothing, since `isProxy` cannot
throw. Written as the ordering mutation it fails three cases.

That is three in two days: a regex that missed `subTest` failures, a mutation
that did not parse, and one that did not express what I meant. The check I now
run before believing a number is whether the mutated source actually says the
thing I claimed to be testing.

### Raised for a ruling, not decided

The same defect exists on a session **reference**, measured rather than
suspected: a Proxy reference runs four `get` traps in
`normalizeAgentSessionRef` and is accepted. That is the signed-off axis on
every observation path here, so refusing Proxy references is cross-cutting
rather than a two-case correction. The disagreement attack there is already
closed — one owned copy — but caller code still runs.

### The fork is now proven

W641's second review has found the same Proxy defect in `agent_handshake.mjs`'s
copy of these rules. Two implementations, the same finding twice. One shared
primitive at W4 composition.

### Verification

- reconnect **32/32**, axis 16/16, turn 50/50, posture slots 25/25.
- `cd v12 && npm test` — **664 tests, 662 pass, 2 fail**; zero test-owned roots
  under a TMPDIR bracket. Both remaining failures are W641's second review, in
  the handshake suite.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting re-review of item 4af.** Open: the runtime and agent adapter
contracts, the W771 posture composition, W151 §9, the Proxy-reference ruling
above, and the shared record primitive.

## Composition revalidation — 2026-08-23

Item 4af was signed off; 4ai asked W4 to consume and revalidate W641's shared
primitive and to revalidate W771's posture lifecycle and W151 §9 in the same
pass. I did that, and the revalidation found things. Evidence:
`evidence/composition-revalidation-2026-08-23.txt`.

### Revalidating a dependency means it would go red if it changed

`agent_reconnect.mjs` consumes `records.mjs` and keeps no copy; I did not edit
that module, which item 4ai reserves to W641. Green suites prove nothing about
a dependency, so I mutated the **shared module** instead: removing its Proxy
test fails 4 reconnect cases, deciding after the traps run fails 3, dropping
the prototype rule fails 5. A relaxation there cannot pass W4's boundary
silently.

### The rule I was taught six times, swept for the first time

Six rounds established that a refusal must never serialize what it refuses.
Each round fixed the one site the reviewer had found. **Nobody swept.**

Measured, by driving every boundary with a BigInt, a circular object, a
throwing `toJSON` and a trapping Proxy: **eleven diagnostic sites across six
modules** still lost the closed pair. All eleven were the same
`JSON.stringify(x ?? null)` line. They are one helper now — `nameValue`,
beside the `ContractError` it builds, calling `records.mjs` for shapes.

And the diagnostic is still worth reading: a string primitive cannot throw, so
a method name is **shown** and bounded; only values with behaviour are reduced
to a shape. Losing "the agent called session/prompt" to "a string value" would
be paying for safety twice.

### A second class the same sweep found

Three READ boundaries bound caller operands straight into prepared statements
— `turnRecordOf`, `eventRecordOf`, `attempts.attemptRow` — so an object
produced SQLite's own binding error and a trapping Proxy an arbitrary Error of
the caller's choosing. Each proves its operand first now, and **absence and
refusal stay different answers**: a well-formed id naming nothing still
answers null.

### Two copies of §3.1 that had diverged, not merely duplicated

`turnSessionRef` **accepted** an empty `providerSessionId` that
`normalizeAgentSessionRef` **refused**. The same reference was valid at one
boundary and invalid at the other. No ruling was needed — the frozen
`$defs.providerSessionId` is `minLength: 1` — and the turn copy had dropped
the word "nonempty" from its check and from its own message. The case that
owns it drives both copies through one table, because the defect was that
nothing compared them.

Reported and **not** fixed: neither copy enforces `maxLength` or `opaqueId`'s
pattern. That changes what is accepted and belongs with the 4ah ruling.

### 4ah: evidence, not a decision

Ordinary accessors run and are accepted; item 4aa's one-read protection holds;
a class instance and even an **array** carrying the four members are accepted;
extra members are accepted and dropped; and the frozen `$defs.agentSessionRef`
is already `additionalProperties: false` over exactly those four. The blast
radius grew by one — this pass routed `eventRecordOf` through the axis
normalizer.

### The suite I should have written six rounds ago

`worker_manager_refusal_taxonomy.test.mjs` — 27 boundaries × 6 hostile
operands, deliberately weak per boundary and strong across them. It does not
say what any boundary decides; it says that whatever it decides, it says so in
the closed pair. The list is **enumerated rather than discovered**, because a
sweep that finds its own subjects stops finding them the day an export is
renamed, and does it silently. The count is asserted for the same reason.

### Verification

- refusal taxonomy **4/4** (new); reconnect 32/32, axis 16/16, turn 50/50,
  posture slots 25/25, events 52/52.
- `cd v12 && npm test` — **676 tests, 674 pass, 2 fail**; zero test-owned roots
  under a TMPDIR bracket. Both failures are W641's third review, which landed
  while this pass was running.
- Eight mutations for this change, all witnessed, plus the three
  shared-primitive mutations above.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting review of items 4ai, 4aj, 4ak and 4al.** 4ah remains an open ruling,
with 4am carrying the measurements it needs. Still unimplemented: the runtime
and agent adapter contracts, and W151 §9.

## Composition correction — 2026-08-23

`review-2026-08-23T20-55-23Z.md`, one P1 and one P2; 4ah stays an open ruling.
Reproduced before any edit: 5 of 7, exactly the two additive regressions.
Evidence: `evidence/correction-composition-round1-2026-08-23.txt`.

### I proved one third of the rule and called it proved

Item 4ak claimed to separate a malformed identity from an absence, and proved
"nonempty string". The frozen `opaqueId` also bounds length at 160 and fixes a
grammar — so a string with a space, or 161 characters, was a legitimate
lookup: the turn read answered **null** and the attempt read went on to a
precondition. **Incomplete in the direction the item was about.**

One proof now, `opaqueIdFault`, called by every boundary that types an
identifier as `opaqueId` — the turn read, the attempt read, the §3.1
normalizer and through it the event reader, and the posture-slot boundary. The
frozen `providerSessionId` bound of 512 goes with it. The **container**
question is untouched; that is 4ah.

### I bounded the branch I had thought about

`nameValue` truncated strings and returned `String(value)` unbounded for
numbers, bigints and symbols — a 1000-character symbol description rendered at
1008. I had been reasoning about whether a value is safe to **convert**; the
rule is whether the result is safe to **keep**.

### The fix would have minted a fresh 4al

`posture_slots.requireAttempt` kept its own "nonempty" check, so fixing only
the boundaries the review named would have made a spaced string a valid
attempt id there and invalid everywhere else — the exact defect 4al was about,
freshly created by the fix for P1. It calls the shared proof now.

**I found it by writing the property test before writing the fix**, which is
the first time this session a case has caught something ahead of a reviewer
rather than behind one.

### One §3.1 copy, not two aligned ones

4al aligned the two texts. **Alignment is a state**: two implementations kept
in step by a regression drift the first time only one is edited, and this
correction was about to edit one. `turnSessionRef` delegates to the axis
normalizer now. The comparison regression is retained and still guards the
boundary pair; the mutation that restores a second copy still fails it.

### A fourth zero that was about my testing

Ten mutations. V9 — the provider bound — measured zero, and it was a missing
case: I enforced the bound and wrote nothing that exercised it. Covered now at
exactly 512 and 513. Four zeros this week: an instrument, a syntax error, and
two missing cases.

### Verification

- refusal taxonomy **9/9**; turn 50/50, axis 16/16, posture slots 25/25,
  reconnect 32/32.
- `cd v12 && npm test` — **682 tests, 682 pass, 0 fail**; zero test-owned roots
  under a TMPDIR bracket.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting review of 4an, 4ao and 4ap.** 4ah is relayed to product authority
and not decided here — what remains of it is purely the container, and it now
has one implementation to change rather than two.

## Composition correction, round 2 — 2026-08-23

`review-2026-08-23T21-08-54Z.md`, one P1. Reproduced before any edit: 8 of 9,
exactly the additive review rows. Evidence:
`evidence/correction-composition-round2-2026-08-23.txt`.

### The bound was right and the ruler was wrong

`.length` counts UTF-16 **code units**; `maxLength` counts Unicode
**characters**. They agree exactly until a string leaves the BMP and then
silently do not: a provider session id of 512 astral characters has a `.length`
of 1024, so it validates under the frozen contract and was refused by the
hand-written proof that exists to be faithful to it.

Item 4an set out to make this boundary faithful, and I made it faithful in the
wrong unit. **I checked the number against the frozen schema and not the
measure.**

One ruler now, and it is fast and exact together — a code point is never more
than one code unit, so a string short enough in code units skips the iteration.

### The same unit at the two other places one is used

Applying it only where the review found it would have been the mistake this
pass keeps correcting, so I looked for every ruler.

The `opaqueId` limit: corrected, and **measured equivalent for the verdict** —
its grammar admits only ASCII, so no astral string is accepted whichever unit
counts. What the wrong unit *did* produce was a false diagnostic, "is 162
characters" about an 81-character string. Reported as equivalent rather than
counted, and corrected anyway.

The diagnostic bound: it sliced by code unit, which can **cut a surrogate pair
in half** and put a lone surrogate into a message that may be retained. No
verdict depends on it and it produces a malformed string, which is worth
fixing on its own terms.

### Something my own first draft got wrong, kept as an assertion

I wrote a row expecting `e` + combining acute + `x` to fit in a limit of two,
reasoning about what renders as one glyph. `maxLength` counts **code points**,
not graphemes: that string is three characters. The row asserts three now, with
the reason beside it — the contract's unit is the one that decides, not the one
that looks right.

### Verification

- refusal taxonomy **10/10**; axis 16/16, turn 50/50, reconnect 32/32, posture
  slots 25/25.
- `cd v12 && npm test` — **683 tests, 683 pass, 0 fail**; zero test-owned roots
  under a TMPDIR bracket.
- Seven mutations, all witnessed, including one that keeps the fast path and
  deletes the exact count — the plausible way this gets broken later.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting review of 4ar.** The review's renumbering is accepted. 4ah and 4ao
remain Slawomir's; the member half is settled either way and now measured in
the frozen contract's own unit, so what remains is purely the container.

## Composition correction, round 3 — 2026-08-23

`review-2026-08-23T21-19-33Z.md`, one P2. Reproduced before any edit: 10 of 11,
exactly the additive regression. Evidence:
`evidence/correction-composition-round3-2026-08-23.txt`.

### A bounded output is not a bounded operation

`bounded` probed the length cheaply — stopping after 61 characters — and then
spread the **whole** string to slice sixty characters off the front. 1,063
iterator steps and a full-size array for a 61-character answer.

I fixed what I could see in the *output* and left the work proportional to what
was being discarded. Round two was about measuring in the contract's unit;
this is the same helper measuring inefficiently. Same mistake at a different
depth: **I checked the answer and not the act.** And it is a refusal path, so
this is "a refusal must not run the value it refuses" one property over.

One pass that stops: at most 61 characters are ever visited, whatever the
caller sent, and the cheap code-unit test in front means an ordinary short
value is not iterated at all.

### A zero I witnessed instead of reporting

The short-circuit mutation measured zero and is a behavioural **equivalence** —
without it the loop still handles short strings correctly, so only the
traversal differs. I witnessed it by counting iterator yields for a *short*
name, the way the review counted them for a long one. An optimisation nothing
observes is an optimisation nothing protects, and this manager has had two
findings in two rounds about work that was invisible because only the answer
was checked.

### Measured, reported, not fixed here

W641's shared `recordFault` interpolates every own member **name** of a
rejected record: a capability envelope with 20,000 members produces a correct
`policy.denied` whose message is **269,042 characters**. Same defect, in the
module W4 consumes. `records.mjs` is reserved to W641 by item 4ai, and W641 had
**closed satisfying** by the time I measured this — so its thread would not
take the report either. Raised as follow-up Work **W1593** instead, with its
own dossier and the measurement, rather than fixing it from here. My new case carries the measurement and the two rows
it should grow once its owner has closed it.

### Verification

- refusal taxonomy **12/12**; axis 16/16, turn 50/50, reconnect 32/32, posture
  slots 25/25.
- `cd v12 && npm test` — **685 tests, 685 pass, 0 fail**; zero test-owned roots
  under a TMPDIR bracket.
- design models 64/66/24/74; v11 pytest 2980 and serial 52; codex-event-bridge
  336; acp-baton-bridge 55; whitespace clean.

### State

**Awaiting review of 4as.** 4at is reported to its owner. 4ah and 4ao remain
Slawomir's and are unchanged by this round.

## Input for the 4ah ruling — 2026-08-23

Item 4as is signed off; W4 is open only on the product ruling. The review also
enabled the two capability rows I had left commented in my property case, so
one property now guards both W4's boundaries and the shared primitive — right
shape, and it means **W4's suite cannot go green until W1593 lands**.

Before routing the ruling I re-measured its facts against the **current** tree,
because the question was raised on measurements taken several corrections ago
and my own role instruction is to revalidate a pinned decision before acting on
it. Evidence: `evidence/ruling-input-4ah-2026-08-23.txt`.

### The facts still hold, and one of them is sharper than I had put it

Accessors run and are accepted; class instances, arrays carrying the four
members and extra members are accepted; item 4aa's one-read guarantee holds.
And **a Proxy reference is accepted** — while the reconnect *options* envelope
beside it refuses a Proxy before any reflection, after six review rounds. Two
operands of one call, two answers to "may a document be a program".

### I measured the cost instead of estimating it

Applied `recordFault(ref, [the four])` temporarily, ran the whole gate,
reverted, and counted every reason it would have refused. 228 refusals — and
they decompose very unevenly:

- **168** are one benign cause: a reference written without
  `providerSessionId`, valid today because the API reads `?? null`. That single
  cause is why all 37 W2929 cases fail under a drop-in.
- Most of the rest are values **already refused today**; the inert proof agrees
  with the current boundary and would only change the reason given.
- Only **eleven** are genuinely new container refusals — a Proxy, an extra
  member, an array.

### Which exposes a third option nobody had named

Whether `providerSessionId` is **required at the API** or
**optional-in-absence**. The cost people would associate with "inert" is almost
entirely that question, not the container question, and the two are separable.
I am not recommending one; I am making sure the decision is taken against what
is actually true.

### State

**Routed to `baton.decide` for the 4ah/4ao ruling.** The member half is done
whichever way it goes, and there is one normalizer to change rather than two.

## Prerequisite revalidation — 2026-08-24

W4 came back on the implementation route because **its ledger dependency
closed** — W2845 is closed satisfying. A dependency closing is not the same
event as an approval landing, and the thread carries no message after the
reviewer's "do not route W4 to implementation yet". So this episode is the
revalidation my role asks for, not a cut. **Nothing was implemented**; no file
under `v12/python` was created or changed.

### Prerequisite one — the Python authority sibling: met

W2845 delivers exactly the object `authority_port.py` was specified to type: an
already-minted, participant-bound session granting no bootstrap, no
configuration, no path and no store handle. Every transition and read the
boundary listed is present, and **`claim_signature` is exported** — which
matters more than its size, because a manager that recomputed it would be a
second authority on whether two claims are the same claim.

The session exposes sixteen transitions and sixteen reads; W4 should type only
the subset it uses, since a port naming more than it uses is a capability
nobody granted.

### Prerequisite two — toolchain and validator: half met

The floor (`>=3.13`) and the hash-locked offline build exist and are proven by
W2845's own gate. But the wheelhouse holds **two artifacts, pip and setuptools**.
`jsonschema 4.19.2` exists only as an ambient system dist-package — which this
boundary itself calls "research evidence, not a reproducible product
dependency" — and the isolated `--ignore-installed --require-hashes` build
stage cannot see it.

**And "add a wheel" is not one wheel.** The minimum runtime closure is six
distributions, and `rpds-py` is a **compiled Rust extension** with no
pure-Python fallback. Provisioning is an environment change, not a file edit. I
did not attempt a network fetch: that is outside what I own.

The frozen schemas are not the problem — both still hash to their canonical
dossier assets and both pass `check_schema` under Draft 2020-12.

### Three options, measured rather than recommended

Provision the wheelhouse (six pinned third-party artifacts in a distribution
whose runtime dependency set is deliberately empty, with a case asserting so);
keep the validator at **test time only**, with the frozen schemas as the oracle
for the exact-POD rules already approved; or narrow cut A to everything except
schema validation. They differ in cost, not in whether they work — so it is a
product call.

### What I did not do

I did not start cut A. Doing the parts that need no validator would be choosing
the third option *by doing it*, which is the kind of decision I have been told
twice this campaign to route rather than take.

### State

**Routed for the approval that never landed**, with the open prerequisite
measured. The frozen Node reference is untouched.

## Cut A, part one — 2026-08-24

The decision route returned W4 to implementation with **no ruling recorded**, no
reply on the thread, and no change to the wheelhouse. Blocking twice with nothing
delivered would be the wrong answer to that, so I looked at what the ruling
actually decides: **one seam**. The package, the schema assets, the POD rules,
the refusal taxonomy, the diagnostics and the canonicalizer are needed under all
three options, so this work cannot be wasted by the ruling going any particular
way.

The validation seam is **absent, not stubbed**, and a case asserts no exported
name claims to validate. I am stating the assumption rather than hiding it: I
read the return to implementation as authorization for the option-independent
core, not as an answer to the validator question.

### The one place a faithful port would have been silently wrong

RFC 8785 orders member names by **UTF-16 code units**. `Array.prototype.sort`
gives the frozen host that for free; Python's `sorted()` orders by **code
points**. They disagree for every document with an astral member name beside one
in U+E000..U+FFFF, because UTF-16 encodes astral characters as surrogate pairs in
U+D800..U+DFFF, which sort *below* U+E000.

Same document, two canonical forms, two digests — and a transliteration would
have passed every test written from the Python side. That is why the 21 vectors
are **generated from the frozen host**: it is the oracle, and a vector written by
the port would only prove the port agrees with itself. All 21 match byte for
byte.

### Four zeros, and all four were my tests

- Removing the float branch still *refuses* — a float falls through to "no
  representation". The branch exists to give section 3.2's **reason**, so the
  case now reads the message.
- The closed-pair guard had nothing to fire on, because every raising site
  spells its pair correctly. The answer is a case that makes the future mistake
  on purpose.
- `OPAQUE_ID_LIMIT = 160` agrees with the schema, so hardcoding it passes.
  Re-expressed as retyping it *wrong*, the case fires.
- **The sharpest one:** the pairing-agreement case compared a *production
  helper* to the schema, and a helper returning the schema's own codes made it
  agree with itself. Both sides are derived in the case now. A test that trusts
  a helper living next to one of its two sources is not comparing two things.

### Two things I chose not to share, and said so in the code

The authority already has `Refusal`, `name_of` and `own`. A rule that exists
twice is a rule that holds in one of the two places — so this was not
comfortable. The refusal **type** differs because a caller must be able to tell
which boundary refused; `own` and `name_of` are **not on the authority's exported
surface**, and reaching past it would break the boundary the two-package split
exists for. Promoting a shared primitive is **raised, not taken**: it changes
closed Work's exported promise.

### One change outside my own files

The build stage asserted the installed origin of the authority only. It now
checks **both** slices and asserts the frozen schema assets **travelled into the
wheel** — package data that never entered the wheel would otherwise fail nowhere,
since a source-tree run reads it from the checkout.

An existing authority case also fired: its isolation test refuses an import
outside the standard library and does not list `importlib`. **I changed my module
rather than their test** — the asset is read relative to `__file__`, correct in
both layouts.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — version, **267 tests**, locked build: all
  pass on Python 3.13.7; 267/267 from the wheel with both slices and both schema
  assets proved to have travelled.
- 21 mutations, all witnessed. 40 regressions added; suite 227 → 267.
- Runtime dependency set still empty; zero temp roots; frozen Node authority
  untouched; whitespace clean.

### State

**Awaiting independent review of cut A part one.** Still open: the validator
ruling, and with it the rest of cut A. Cuts B–F and `authority_port.py` are
absent on purpose.

## Cut A complete — 2026-08-24

Two P1, one P2, all reproduced before any edit, all closed with the reviewer's
three regressions retained. Plus the acceptance gap: PLAN 4bh's ruled validator
and 4bi's authorized test migration.

### Naming a type ran the caller's metaclass

A class is an instance of its **metaclass**, so `type(value).__name__` is
ordinary attribute dispatch — and the one helper whose entire job is to describe
a rejected value *without running it* was doing exactly that.
`type.__getattribute__` skips the override. Probing my own correction then found
**two more shapes it does not close**: a metaclass `__name__` descriptor that
raises, and one that answers non-text. Both were mutations with no witness until
I wrote the case.

### A closed set a caller can open is not closed

The pairing is private and frozen now, with the readable vocabulary beside it
and a case proving they agree — the residual risk of the two-value shape, named
rather than left. The reviewer's regression opens a **code**; opening a whole
**category** was a second escape their code-only case could not see.

### Bounded operation, bounded output

The bound was on the escaper's *input* and `ascii()` expands an astral character
to ten. Both now.

### The ruled validator

`jsonschema` 4.26.0 with its **measured** five-distribution closure (not the six
the older version needed), hash-locked from the artifacts themselves, installing
offline under `--require-hashes`. The wheelhouse moved into the distribution
because the system one holds two artifacts and is **not writable**. Whether 3.2 MB
of wheels are *committed* is raised, not answered — the tree carries essentially
no binaries today, and that is a repository-shape call.

The library decides the contract; this package decides the diagnostic.
`error.message` is never used, ownership runs first so the validator only walks
exact built-ins, and **combinators are followed to the failure underneath them**
— my own case found that, because "the document breaks oneOf" is true and helps
nobody. The same case caught my accept-path fixture being rejected and therefore
**skipping**, which is the silent-acceptance weakness I have been caught on
before.

### The authorized migration

Three authority cases asserted the distribution's dependency set was empty. A
case asserting a superseded state argues for the old answer every run — so the
import scan is scoped to the authority slice, "pins no validator" became a scan
of the authority's own source (a file that does not mention a library and a
slice that does not reach for one are different facts), and "the lock is empty"
became "the lock says whose its pins are". My own superseded class went too.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **297 tests**, all pass on Python 3.13.7;
  297/297 from the wheel with the ruled validator installed offline.
- 19 mutations, 16 witnessed. Four began as zeros: three were missing cases, and
  the fourth — the sampling cap — is **unreachable** against the whole schema, so
  the case went where it can be reached rather than pretending coverage.
- Three equivalences reported with reasons; 30 regressions added (267 → 297).
- The frozen Node oracle is untouched and still runnable.

### State

**Awaiting re-review of the complete contracts cut.** Cuts B–F and
`authority_port.py` remain absent on purpose. Open for the reviewer: whether the
wheelhouse artifacts belong in the tree.

## Cut A correction — 2026-08-24

Four P1 and one P2, all reproduced before any edit, all closed. The reviewer's
five methods are retained and the earlier three remain green.

### The same line, corrected twice

Round one: `type(value).__name__` ran a metaclass `__getattribute__` override.
Round two: `type.__getattribute__` skipped the override and **still invoked a
data descriptor** the metaclass installed as `__name__`.

Both are one defect stated two ways: **any lookup that consults the metaclass
consults the caller.** I corrected the mechanism I had been shown instead of the
rule underneath it — the same mistake as fixing only the site a review names,
now made at the level of a single expression. The name binds
`type.__dict__["__name__"]` directly, so the metaclass is not consulted at all.

My own previous case was superseded by the fix and is **strengthened** rather
than deleted: the property is now that a metaclass descriptor neither runs nor
changes the answer.

### Privacy is not an isolation boundary — and my comment said so

`_PAIRING` had frozen member sets and an ordinary mutable outer dict, while the
comment beside it promised "frozen all the way down". The authority's session
face says the same thing about underscores in as many words. **I wrote the
promise and did not implement it.**

### Two doors still took a caller program

`validate_against` invoked any supplied object's `iter_errors` — the document was
owned first, so a caller could not smuggle a *container*, and nothing stopped it
smuggling a *validator*. The check is **identity, not shape**: asking whether it
has `iter_errors` would be asking the attacker to confirm their own credentials.

The subtler one: the validators were built over the same dicts exported as
`WORKER_CONTROL` and `AGENT_SESSION`, so editing the readable projection rewrote
what the runtime enforced. Nothing was "supplied" at all. **A projection that can
rewrite what it projects is not a projection.**

### One rule, two public doors, enforced at one

`own` enforced the frozen depth and width; the equally public canonical surface
enforced neither, so a document `own` refuses could still acquire a digest. That
is the shape this repository has now caught me in **five times**. The bounds live
with the canonicalizer and `pod` takes them from there — one definition, both
doors — and depth is checked *during* the descent so extreme nesting cannot
escape as a raw `RecursionError`.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **302 tests**, all pass on Python 3.13.7;
  302/302 from the wheel with the ruled validator installed offline.
- Nine mutations, all witnessed, **no zeros**. P6 is worth naming: dropping a
  bound and failing to *carry* it are different defects.
- Both stale statements corrected, each saying what it replaced.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting another bounded review.** The wheelhouse arrangement is unchanged, so
the reviewer's repository-shape proposal stays open for Slawomir. Cuts B–F and
`authority_port.py` remain absent on purpose.

## Cut A — the caller could choose the traversal state — 2026-08-24

Reproduced first: `canonical_text(deep, -MAX_DEPTH * 2)` and
`own(deep, _depth=-1000000)` both walked straight past the frozen depth. Closed;
the reviewer's two methods are retained.

### A leading underscore names a convention, not a boundary

The previous correction **shared** the depth and width bounds across both public
doors, because a rule applied at one of N sites is not applied. It then left the
*enforcement state* of that shared rule as a parameter of both public functions
— so a caller could hand the descent a negative starting point and walk past the
bound the correction had just finished sharing.

**The bound was shared and its state was not.** That is the same defect one level
lower, and it is the second round running in which I corrected the mechanism a
review named rather than the rule underneath it — last round a single expression,
this round a single parameter.

### So the rule is checked, not the two functions

Fixing the two functions a review names is what I have been caught doing five
times. A standing case now refuses any public operation whose parameters are
bookkeeping rather than declared operands, with the permitted names written out
(deriving "is this an operand" from a name is the guessing the case exists to
stop) and its own vacuous-pass modes refused.

Measured: a future `digest(value, seen=None)` — an ordinary-looking parameter
with no underscore at all — fails it. That's the half an underscore check would
have missed entirely.

### Seven mutations; two needed work, with different answers

- **A missing case.** Every label case went through `own_record`, which bounds
  the label itself — so `own`'s *own* bounding was never measured, and a caller
  reaching `own` directly was relying on a guard nothing tested.
- **A genuine redundancy, removed rather than reported.** My separate
  "no underscore-named parameter" case changed no verdict in front of the
  operand case, because an underscore-named parameter is not a declared operand
  either. It is also the weaker statement.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **307 tests**, all pass on Python 3.13.7;
  307/307 from the wheel with the ruled validator resolved offline.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of this narrow correction.** The wheelhouse arrangement is
untouched, so the repository-shape proposal reaches Slawomir undisturbed.

## Cut B — the control store and the manager's journal — 2026-08-24

PLAN item 4bc, after cut A's sign-off. The separate store with its own **store
kind** marker, the operation journal, transactional CAS, exact replay and
collision, real-process races and restart. The frozen host's fifteen state tables
are **absent**: a table nothing writes is a claim about a design rather than part
of one.

### Obligations ported with their corrections intact

**Presence is its own fact** — the frozen host answered `null` for both "no row"
and "the committed result was JSON null", so an exact retry of a null-returning
operation looked new and ran the action twice. **Ownership, not presence** — a
database holding `foreign_state` was *adopted*, because absence of our metadata
was read as proof the file was new. **The whole sealed refusal** — only the
message was kept, so a durable `policy.retention` replayed as
`refused.precondition`: a different answer with a different retry policy.

I added one thing beyond the port: the **store kind**. Version 1 is true of the
authority's store and three files beside it, so kind is checked before version —
the same correction the authority slice got, applied before anyone had to find it
twice.

### Two defects I found in my own code by running it

**The journal row was never written.** My first draft committed the action's
writes and recorded nothing, so the retry ran the action a second time and
returned a different answer under one operation identity — effectively-once,
implemented to do the opposite. The first thing I ran caught it.

**`executescript` commits before it runs**, which would have ended the
transaction the DDL is supposed to be atomic inside.

### Three zeros, three different answers

- **A case that proved nothing.** It wrote to the refused file from another
  connection — but a leaked connection with no open transaction holds no lock, so
  the write succeeded either way. It counts this process's **file descriptors**
  now, and a second case covers the path where the handle is already open when
  the refusal happens.
- **My own ill-formed mutation** (`except ZeroDivisionError if False else
  BaseException` still catches everything).
- **A window four racing processes did not land in.** A case opens it on purpose:
  a competing connection commits during the peek, and the manager must return the
  winner's answer without running its own action.

### The race proves it raced

Every child replays the same answer, so the answers alone cannot say whether four
processes contended or one ran four times. Each reports its **own pid**.

### A hygiene check that could not attribute what it counted

My temp prefix was `v12-manager-`, which is also the frozen Node suite's — and
that suite left **435 roots** here on 2026-08-22. Renamed to
`v12-worker-manager-`; this run leaves zero, and the 435 are visibly somebody
else's.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **334 tests**, all pass on Python 3.13.7;
  334/334 from the wheel.
- 16 mutations, all witnessed. 27 regressions added (307 → 334).
- Zero temp roots from this run; frozen Node oracle untouched and still runnable;
  whitespace clean.

### State

**Awaiting review of cut B.** Cuts C–F and `authority_port.py` remain absent. The
wheelhouse repository-shape ruling is still open for Slawomir.

## Cut B correction, and the dependency-distribution ruling — 2026-08-24

Three P1 and one P2, all reproduced first, all closed, the reviewer's four
methods retained. Plus PLAN item 4bp.

### I wrote the rule down and then broke it two functions later

`transact` re-reads inside the lock, and the comment explaining *why* is mine:
two managers can pass the optimistic peek concurrently. `open` decided emptiness
**outside** the lock — so when several managers saw one fresh database as empty,
the first created the schema and every waiter resumed into the same
`CREATE TABLE`.

The same sentence, the same file, applied at one of two sites. Fifth time this
campaign, and the first time I'd already written the rule in the module where I
then failed to follow it.

### A name is not permission

`meta(id INTEGER)` was treated as licence to `SELECT key, value FROM meta` and
escaped as a raw SQLite error. The probe runs inside the taxonomy now — and the
two foreign shapes are **told apart**, because "no metadata" and "a meta we
cannot read" are different facts and the second message is wrong about the first.

### Two caller accounts of one fact

The kind lives in the journal *and* inside the signature, and neither was
compared — so a retry with the same signature and a different kind replayed the
first success. Bound at the write **and** compared at replay: the write-time
check makes the replay comparison unreachable from the public path, and a store
is not the only thing that writes to a store.

### Impossible state, rejected by the store

One CHECK; JSON `null` stays the text `"null"` so it's distinct from SQL NULL.
The version went to **2** with it, because a store written under the weaker table
cannot satisfy the rule this build enforces. **The invariant caught two of my own
fixtures**, which is the argument for putting it in the schema rather than the
writer.

### Item 4bp, and the download that was refused

The wheelhouse is gone; a disposable venv downloads the locked closure under
`--require-hashes`. The wheelhouse case became `TheHashesAreTheArtifactsOwn` —
mechanism superseded, **property kept**.

**The first locked download after the ruling was refused.** `pip` and
`setuptools` had been hashed from Debian's repackaged wheels, because under the
offline arrangement those *were* the artifacts; the index serves different bytes
for the same version. Both re-measured. The refusal is the mechanism working: a
hash is a fact about bytes, and the bytes changed when their source did.

### A defect in my own gate, found while doing this

**The source stage resolves the ambient `jsonschema` 4.19.2 while the lock pins
4.26.0.** A green source run had been proving the code against a version this
distribution does not pin — quietly, for two rounds, including in evidence I
wrote. The arrangement is defensible; the silence was not. The stage now prints
what it resolved, the pinned-version case reports instead of skipping invisibly,
and a case asserts the gate includes the locked stage. Inside that environment
nothing skips.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **346 tests**, all pass on Python 3.13.7;
  346/346 inside the locked environment with nothing skipped.
- 17 mutations, all witnessed. Six began as zeros: five missing cases, and **one
  case that measured prose** — it searched the whole justfile for
  `--require-hashes`, which the comment above the command contains. Third time in
  this Work a check has been caught measuring a spelling.
- 12 regressions added (334 → 346); no wheel, sdist or archive anywhere under the
  distribution; zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of cut B.** Cuts C–F and `authority_port.py` remain absent.

## Cut B — a signature this manager could not have produced — 2026-08-24

One P1 and one P2, both reproduced first, both closed, the reviewer's two methods
retained.

### Checking that two accounts agree is not checking that either is true

The previous round bound the kind to the signature — the right fix for that
finding, the wrong **depth** for the rule. `_agreeing` then asked "does this
parse, and does its kind match?" Both questions are about *agreement*; neither
asks whether the thing agreeing is a signature this manager could have written.

So an indented spelling, a document with no `operands`, and one carrying an extra
member all passed and became durable identities. Equivalent operations could
acquire **different byte identities**, and data outside the defined operand set
could enter collision and replay identity.

The signature is now owned as exact POD, required to carry exactly `kind` and
`operands`, and compared **byte for byte** against the canonical serialization of
that owned document — all before the journal transaction opens.

### Stale prose is a wrong answer, and this was the second time

I revised two docstrings and the lock header for item 4bp and left the gate's own
text saying the lock resolves offline, that build isolation would reach the
network, and that the gate refuses without a wheelhouse. A reader who trusts a
comment describing a mechanism the tree does not have **has been told something
false by the tree itself**.

So the rule is checked now. And the check's first version was wrong instructively:
it scoped the historical marker to a *paragraph*, and the live sentence shared a
comment block with the historical note — so the escape hatch swallowed exactly
the drift it was written to catch, and the mutation measured zero. Line-scoped
now. `--no-index` is deliberately **not** on the removed list: the second install
uses it correctly, and banning a word is not banning a mechanism.

### Seven mutations: four witnessed, three measured equivalent

The equivalences are reported with reasons rather than shrugs — the extra-member
shape check is subsumed by the byte comparison (kept for the accurate message),
`own` over an already-inert parse is defence in depth, and moving the check after
`replay` changes nothing *today* because `replay` writes nothing, which would
stop being true the moment it did.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **349 tests**, all pass on Python 3.13.7;
  349/349 inside the locked environment with nothing skipped.
- 3 regressions added (346 → 349); zero temp roots; frozen Node oracle untouched;
  whitespace clean.

### Raised, not acted on

The reviewer's independent `just build` could not reach the configured index, so
their locked stage stopped before installing. That is the ruling working as
written — and it changes **who can run the full gate**: a managed turn without
egress can prove the source stage and not the locked one. The ruling anticipates
an operator cache or certified bundle, but nothing in the tree arranges one and I
am not inventing it. Recorded so the gap is not rediscovered.

### State

**Awaiting re-review of cut B.** Cuts C–F and `authority_port.py` remain absent.

## Cut B — what reaches a TEXT column must be durable text — 2026-08-24

One P1, all four shapes reproduced first, closed; the reviewer's method retained.

### The third thing

The last two rounds established that the two accounts of the kind **agree**, and
then that the signature **is one this manager could have produced**. Neither
establishes that the value entering a column the schema types as TEXT is durable
text.

The integer case is why that isn't implied: `7` agreed with itself, produced a
perfectly canonical signature, **committed** — and SQLite stored `"7"`, so the
operation could never be replayed by the caller that created it. `None` hit the
NOT NULL column as a raw `IntegrityError`, `""` committed as an unnamed kind, and
a hostile operand ran its `__eq__` from inside a boundary that had already
decided to refuse.

`durable_text` is that rule in one place, run **before** any comparison —
`type(x) is str` touches no caller code.

### It applies at six sites, not one

The review named the kind. A sweep found the same `UnicodeEncodeError` leaking
from the operation identity, the settled instant, the sealed refusal text, and
**both read paths**. Sixth time this campaign, second time in this cut — so the
sweep is the fix, not the single substitution. `manager_signature` proves it too:
a helper that can build an identity the store must refuse invites the caller to
discover the rule by hitting it.

### Two things my own cases taught me

The **reads** faulted on an identity they were checking was absent — a lookup for
something that cannot exist should refuse, not fault. And the **clock is proved
at open**, earlier than I wrote the case for; that's better than what I was
testing for, so the case asserts it where it happens.

### Nine mutations, eight witnessed, one equivalence — and I corrected the comment

I had written that sealing before releasing the savepoint is what stops an
unsealable durable refusal keeping its writes. Measured: swapping the order
changes nothing, because the **rollback** in the outer handler is what protects
them. The ordering stays for a smaller true reason. A comment claiming more than
the mechanism does is the same defect as prose describing a mechanism that is
gone — which this cut was corrected for once already.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **352 tests**, all pass on Python 3.13.7;
  352/352 inside the locked environment, nothing skipped.
- 3 regressions added (349 → 352); zero temp roots; frozen Node oracle untouched;
  whitespace clean.

### State

**Awaiting re-review of cut B.** Cuts C–F and `authority_port.py` remain absent.

## Cut B — I widened a helper into a hazard I had already closed twice — 2026-08-24

One P1, both shapes reproduced first, closed.

### The defect was the export, not the code

`_durable_text` was correct where it was called from — every label reaching it is
one of this module's own literals. What made it a boundary was **adding one name
to two `__all__` lists**.

A diagnostic label is this package's prose at an internal call site and **caller
input the moment the function is exported**. That distinction is invisible in the
function body, which is why it keeps being missed: the authority slice was
corrected for ten exported helpers whose labels were interpolated raw, and I
recreated the class here by widening a surface no caller had asked for.

The helper is private and unexported now — the review's preferred resolution and
the smaller change.

### And the rule is mechanical now, because remembering it has failed twice

`AnExportedLabelIsCallerInput` resolves every name in both packages' `__all__`
and requires any exported function taking a label to bound it — or not be
exported.

**Its first run found two more.** `validate_worker_control` and
`validate_agent_session` pass `what` to a body that bounds it, so they were *safe
in effect* and still broke the rule's letter: a property that holds only because
of what a callee happens to do is a property that holds where somebody looked.
They bound their own label now; `label_of` is idempotent.

That's the difference between fixing a finding and closing a class — the review
named one helper, and the check found the two it didn't, and would have refused
the export that caused this one.

### One instrument error, mine

A blanket text rename turned the *definition* into `__durable_text` while every
call site became `_durable_text`, and 38 cases errored at once. Loud, immediate,
and my own — recorded because the useful observation is that a rename is a
refactor and I did it as a search-and-replace.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **355 tests**, all pass on Python 3.13.7;
  355/355 inside the locked environment, nothing skipped.
- Four mutations, all witnessed, plus the reviewer's conditional method firing on
  a re-export.
- 3 regressions added (352 → 355); zero temp roots; frozen Node oracle untouched;
  whitespace clean.

### State

**Awaiting re-review of cut B.** Cuts C–F and `authority_port.py` remain absent.

## Cut C — the offer and the claim — 2026-08-24

PLAN item 4bd, after cut B's sign-off. The injected authority port, the offers
table at schema version 3, and the whole offer/claim boundary through to
asymmetric restart recovery.

### Two decisions I made rather than inherited

**The port names only what W4 uses.** The session carries sixteen transitions and
sixteen reads; a port naming all thirty-two would be a capability nobody granted.
Five members is what cut C needs, and a later cut widens it deliberately.

**The claim signature arrives by injection, not by import.** The manager must not
recompute it — that would make it a second authority on whether two claims are
the same claim. But importing the sibling package would make it depend on the
authority's module graph to do arithmetic on a string, while the deployment that
mints the session already holds the authority and can hand the derivation over
with it.

### Item 4bd's own sentence, as a case

"No adapter write occurs while claim outcome is ambiguous" — so the `live` answer
writes nothing and says so. Two mutations witness it.

### A defect my own fixture found

The one-live-offer-per-Work index escaped as a raw `sqlite3.IntegrityError`. A
manager losing that race is having an *ordinary precondition* refused, and
telling it so in SQLite's vocabulary would make a caller learn our taxonomy from
a driver. **And the case that should have caught it was mine, written as
`assertRaises(Exception)`** — the weak assertion I've criticised in other
people's cases. It names the closed pair now, and naming it is what found the
defect.

### Six zeros, and half of them were my instrument

- **Certification optional** — the other branch refused with the *same code*, so
  the case had to read the reason. Two refusals sharing a code are two answers.
- **The authority in the signature** — my case varied *two* things: it also
  advanced the clock, and `expires_at` is signed too. A case that varies two
  things measures neither.
- **The frozen claim signature** — my mutation was `None or X`, which is X.
- The other three were missing cases: the concurrent commit marker (window
  opened on purpose), and the terminal CAS, which **expiry makes reachable
  against an `accepted` row** — so a stale expiry really can destroy a frozen
  claim identity.

### The operand sweep caught its own proxy

My declared-operand check required the list to stay smaller than the surface — a
proxy for "the list must not become the answer". Cut C made that proxy *wrong
rather than strict*: a package can legitimately have more operand names than
functions, and the ratio then fails for growth instead of laxity. Measuring the
wrong thing strictly is not rigour. The property is stated directly now.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **393 tests**, all pass on Python 3.13.7;
  393/393 inside the locked environment, nothing skipped.
- 28 mutations, 26 witnessed; two equivalences reported with reasons.
- 39 regressions added (355 → 393); zero temp roots; frozen Node oracle
  untouched; whitespace clean.

### State

**Awaiting review of cut C.** Cuts D–F remain absent on purpose.

## Cut C correction — I wrote a weaker copy of my own rule — 2026-08-24

Three P1 and one P2, all reproduced first, all closed; the reviewer's five
methods retained.

### The one that matters most is the one I wrote myself

Cut B established `_durable_text` and applied it at **six** sites, and I wrote
the evidence saying so. Cut C then declared a **local, weaker `_text`** one file
over — accepting lone surrogates and treating any nonempty string as an instant.

Seventh time this campaign a rule has been applied at one of N sites, and the
first where the other site was **mine, and three days old**. Writing the rule down
didn't stop me; having it in a different module didn't stop me. There's no local
rule now.

**And the instant is a second property**, not a stronger first one: encodable text
keeps a value out of SQLite's way, the frozen grammar keeps it out of a
*comparison's* way. The clock is held to both now — every deadline this manager
compares derives from it, so cut B's "storable" was half the question there too.

### A capability discovered missing once durable state depends on it was never typed

The port checked that its members **exist**. A session whose `claim` is `None`
constructed, issued and accepted — then failed as a `TypeError` after the claim
identity had been frozen, which is the one moment the manager cannot retreat
from. Operations must be callable at construction; `participant` stays a bound
value.

### A duration is an operand, and a comment is not a constraint

A negative `ttl_seconds` minted a bearer and committed durable authority nobody
can use. And the offers CHECK named three fields while its comment said five, and
constrained only one state — so an `accepted` row could omit its whole identity
and an `issued` row could carry acceptance deadlines. Schema version 4.

### Fifteen mutations; three zeros were missing cases, one was a redundancy

Missing: a clock answering *prose*, the acceptance **deadline** half of the
invariant (the reviewer's row omits all five, so a CHECK naming three still
refuses it), and **every** earlier schema version rather than the first — my
version cases named v1 while the build had moved to 4.

**The redundancy I removed rather than reported:** I wrote `type(x) is bool or
type(x) is not int`, and `type(True)` *is* `bool`, so the first clause can never
decide anything the second doesn't. Measured, then deleted — a guard nothing can
see is worth less than the line it costs.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **400 tests**, all pass on Python 3.13.7;
  400/400 inside the locked environment, nothing skipped.
- A sweep of every SQL and time boundary in cut C: all seven refuse with the
  closed pair.
- 7 regressions added (393 → 400); zero temp roots; frozen Node oracle untouched;
  whitespace clean.

### State

**Awaiting re-review of cut C.** Cuts D–F remain absent on purpose.

## Cut C — my sweep measured my imagination — 2026-08-24

Two P1, both closed, the reviewer's four methods retained.

### The finding behind both findings is my own evidence

Last round I wrote: *"I also swept every SQL and time boundary in cut C rather
than fixing the two you named: all seven refuse with the closed pair."*

True about the seven I called; false about the claim it made. **I probed the
entry points I could think of.** The review enumerated the code and found six
more — two claim paths looking offers up by unproved identity, an optional Work
filter, both certification key parts, and the injected signature's *answer*.

Cut B's sweep was real: it walked the SQL statements and the AST. Cut C's was
recall wearing a sweep's clothes — and the difference didn't show in the evidence
because both were written the same way. **Probing measures imagination;
enumeration measures the code.**

### Fixed at the owning boundaries, as the review specifies

The lookup proves its identity in `_offer_row` rather than at each caller —
proving it at each caller is *how* a rule ends up applied at some of its sites.
The optional filter is proved, because an optional operand is exactly what a
sweep by recall misses. Both certification key parts are proved, because
**canonicalizability is not durable text**: an integer canonicalizes happily and
commits into a metadata key. And the injected derivation's *answer* is proved: a
capability is trusted to be the authority's, not to be correct.

### Representability is a third property

`10 ** 100` is an integer and positive and not a duration this domain can
express. It belongs to the **sum**, not either operand — and the deadline is
computed before the authority is read at all now, which makes "before reads or
entropy" true rather than nearly true.

### And the sweep is derived now, because twice is a pattern

Every exported callable must appear in a table with one minimal valid call and
its text operands named; each is driven with a lone surrogate. **A completeness
case asserts the table names every exported callable**, so adding one without
adding a row fails the gate. The judgement stays where a person can see it; the
enumeration goes where a person cannot forget it.

Measured: removing the proof at each of the four boundaries fails this sweep —
including the two the review found that I had never called.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **407 tests**, all pass on Python 3.13.7;
  407/407 inside the locked environment, nothing skipped.
- Seven mutations, six witnessed; one equivalence, where the comment now claims
  the smaller true thing (`datetime` cannot reach a year the grammar rejects, but
  a five-digit year would sort *below* a four-digit one, and every comparison
  here is lexicographic).
- 7 regressions added (400 → 407); zero temp roots; frozen Node oracle untouched;
  whitespace clean.

### State

**Awaiting re-review of cut C.** Cuts D–F remain absent on purpose.

## The centralized boundary layer — 2026-08-24

The anti-loop gate (4bx/4by) asked for a redesign, not another patch. Cut D stays
unstarted.

### Why the loop happened, in one sentence

My inventory came from **recall**, and my probes proved that *a* refusal happened
rather than proving **which boundary** refused. So each round I fixed the named
sites, claimed a sweep, and the same class survived where I hadn't looked.

### The layer

`boundaries.py` owns five kinds — text, identity, instant, deadline, injected —
and **every refusal names its boundary**. That label is not decoration: it's how
a probe proves it arrived, and it's what makes vacuity detectable at all.

**An instant is three properties.** Fixed-width digits don't establish a
calendar: `2026-99-99T99:99:99.999Z` had the shape, escaped `strptime` as a raw
`ValueError` on the arithmetic path, and on the comparison path was never parsed
— it sorted after every real deadline and silently expired a live offer. And the
calendar doesn't establish the grammar: **`2026-8-24T0:0:0.1Z` is a real moment,
parses cleanly, and sorts wrong** — "2026-8-24" orders after "2026-12-01".

### The inventory is derived, not recalled

An AST walk collects every `boundaries.<kind>(…, "<label>")` call and attributes
it transitively to every exported operation that can reach it: **ten operations,
twenty-eight boundaries, none listed by hand.** A boundary call with no literal
label *raises* rather than being skipped.

**It found two things on its first run** — exactly what it's for: a hand-written
copy of the text rule sitting *beside* the layer (so a probe aimed at its label
was refused by a rule the inventory couldn't see), and **a loop that hid seven
labels** from any walk. The loop is unrolled: a rule that is applied and cannot
be *seen* to be applied is a rule the next reviewer takes on trust.

### Every probe proves it arrived

Each probe establishes real preconditions and asserts the exact label. A probe
refused earlier sees a different label and fails — and the guard is itself proved
by driving the review's own vacuous shape.

**What cannot be probed is declared with its reason**, and each claim is
*checked* by spoiling the operand that would reach it and requiring the earlier
boundary to refuse first. An unreachable entry is a claim a reviewer can check,
not an opt-out.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **417 tests**, all pass on Python 3.13.7;
  417/417 inside the locked environment, nothing skipped.
- Twelve mutations, all witnessed — three of them the machinery checking itself
  (a boundary that stops naming itself, a derivation that stops being transitive,
  a probe that stops checking its label). One began as a zero and produced the
  padding finding.
- 10 regressions added (407 → 417); zero temp roots; frozen Node oracle
  untouched; whitespace clean.

### State

**Awaiting re-review of the redesigned boundary and its inventory as one unit.**
Cut D remains unstarted, as the gate requires.

## Three domains, not one — 2026-08-24

The review found three P1s and they were one defect. `caller` was the only
receiving trust domain I had ever *named*, so every correction round had been
spent patching sites inside it — while two whole domains crossed the boundary
with nothing owning them at all. Malformed adopted rows escaped `replay` as a
raw `JSONDecodeError`, from the one function whose whole job is handing a retry
the first answer. An integer projection faulted at `.get`. An integer claim was
*persisted* as the assignment. An integer settlement was read as `live` — the
branch that writes nothing — so "we do not understand this" silently became "the
identity is still open", which is a claim about the authority nobody made.

`DOMAINS = ("caller", "adopted", "injected")`, and three kinds to carry them:
`document`, `alternative` (a closed discriminated set, because the point of a
closed set is that a value outside it is a refusal rather than the least alarming
member) and `adopted`. Every injected answer is owned **at the port**; every
adopted payload **at the decode**, which is where the domain is crossed.

### The half of the ruling that is deletion

4bz forbids blanket revalidation as plainly as it requires ownership, and the
double validations were mine — `deadline` re-owning both its from-instant and
its own answer, `accept_offer` owning an id twice, `issue_offer` re-owning a
uuid the projection had owned.

The from-instant one is the one worth keeping. Last round I wrote it up as an
"unreachable entry, with its reason", and that sounded like rigour. It was not.
It was me documenting a double validation as though it were a defended edge.
**A boundary no caller can drive is usually a boundary that should not be
there** — and my list of unreachable-with-reasons was, read honestly, a list of
places I had validated twice.

### An inventory that can find what is missing

The third P1: my inventory derived its universe *from the validators*, so an
entry with no validator was invisible by construction — it could only ever
confirm that the things I owned were owned. Entries are now read from the code
independently: 55 (52 caller, 2 adopted, 1 injected) against 36 owned subjects,
25 stated pairings, 9 delegations. Putting the universe back on the validators
now fails 32 cases. It failed none before, which *is* the measurement of the P1.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **425 tests**, all pass on Python 3.13.7;
  the same 425 inside the locked environment.
- Ten mutations: eight witnessed. Two began as zeros and were **missing cases**
  of my recurring shape — no test had ever driven a non-text slot holder, and
  none had ever supplied a settlement `kind` outside the four, which is the
  precise hazard the closed set exists for. One, the owned-twice guard, is a
  **real equivalence** and is left as one: it has nothing to catch today, so
  what is proved instead is that its counting would see a second claim.
- 8 regressions added (417 → 425); zero temp roots; frozen Node oracle
  untouched; whitespace clean.

### What is not done

**4bz's closed canonical constructors for outbound documents are unimplemented.**
Every operation still assembles its answer as an inline dict. I named this gap
answering poke=4478 and I am naming it on the way out rather than letting "4bz
addressed" stand for it.

### State

**Awaiting re-review of the trust-domain boundary and its code-derived inventory
as one unit.** Cut D remains unstarted, as the gate requires.


## I corrected the instances and left the model — 2026-08-24

Three P1s, and they said one thing about the round before them. I had added the
adopted and injected domains, closed the six defects a review demonstrated, and
reported it done. What I had actually done was fix the *instances*: the adopted
universe still began at `boundaries.adopted` calls, so a persistent read with no
validator produced no inventory row — **the exact circularity the previous
review rejected, moved one domain over rather than removed**. `document`
rejected missing members and accepted every extra one. `alternative` closed the
vocabulary and left every variant's shape open, so `{"kind": "committed"}` was a
complete settlement and an offer advanced to `claimed` carrying a null
assignment. And the probe gate iterated the old global label table while the
inventory was keyed by entry, so nothing required an entry to have a probe.

### The universe now comes from the SQL

Every `execute` is parsed and every SELECT kept, keyed by the table it names —
a structure that exists whether or not anybody owned the result. Five crossings.
`boundaries.row` owns a row's **column set** as well as its values, against a
per-table contract that sits beside the DDL: the CHECK constraint binds what
*this* build writes, and an adopted row is by definition one some other process
wrote. The three offers-table read sites became one, because three sites is
three chances to forget.

`sqlite_master` is declared with a reason instead of owned. I wrote a
`boundaries.text` there first and could not drive it — and a boundary no caller
can reach is exactly what my last round was corrected for.

### Closed means closed both ways

An extra member has two readings and both are alarming; ignoring it silently
picks the happier one. Each settlement variant now carries its own contract,
because knowing *which* answer arrived tells you nothing about what it must
carry. The projection contract is split into the five members the manager reads
and the ten it knows the authority emits — and that split is checked against the
**authority's own source**, not against the fake.

### One key, three questions

An entry is `(domain, lexical site, subject)` — module, class, function. The
universe, the owner and the probe are looked up by the same tuple. 58 entries,
43 probes, 28 stated owners each naming a witness that must exist, 5 delegations
whose label is read from the delegate's own code.

Building it corrected two things **I had written down wrong**: `replay`'s kind
and signature are compared against the journalled row rather than delegated, and
a decline's reason rides the manager signature rather than reaching SQL unowned.
Both found by the machinery rather than by a reader, which is the first time
that has happened in this campaign.

### The outbound constructors, finally

Owed for two rounds and named in my own handoffs. `_settle_terminal` answers one
document when its compare-and-swap wins and another when it loses;
`_record_claim` is reached from four callers each contributing its own members.
So the shape of an answer was a property of the **path** rather than of the
operation — and a document whose members depend on the branch that built it
cannot be owned at the far end against anything.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **455 tests**, all pass on Python 3.13.7;
  the same 455 inside the locked environment.
- Sixteen mutations, fifteen witnessed. Five began as zeros. Four were **missing
  cases**: the column-set half of `row` (every probe I had written corrupted a
  *value*), and three about outbound **stability** rather than outbound refusal
  — these answers are journalled, so member order and the difference between an
  omitted optional and a null one are durable facts I had never asserted. The
  fifth was the projection contract, where the fake agreed with the contract and
  the authority had never been asked.
- One **real equivalence**, left as one: every entry has a probe, so the
  assertion saying so has nothing to catch. That the pairing would *notice* a
  missing probe is its own case.
- 30 regressions added (425 → 455), including the reviewer's three retained
  ones, which now pass at the central model rather than at three patched sites.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of the centralized model and its inventory as one unit.**
Cut D remains unstarted, as the gate requires. Nothing under 4bz is outstanding.


## An exclusion nobody checks is a hole with a comment over it — 2026-08-24

Last round I made the universe structural for the domain a review had
demonstrated. This round's finding is that the structure I chose was still a
*subset of the language*: ordinary positional and keyword-only parameters,
capability calls and SELECT statements — three of the forms a value can arrive
in, presented as all of them.

What fell through was not hypothetical. An unencodable bound participant
constructed happily, because the inventory saw the session's *calls* and never
`session.participant`. A non-callable bearer mint performed a projection, a
certification check, expiry processing and a capacity read before escaping as a
raw `TypeError` — and it was excluded from the universe **by name**, on the
grounds that capabilities are owned at their constructors, while no constructor
owned it. And nine public constructors take `**members`, absent from an
inventory that claimed to hold every public parameter.

`NOT_INPUTS` is now `{self, cls}`. Every signature form is read; a capability's
bound *value* is its own entry; a capability *operand* is an entry whose owner
is named — and `CONSTRUCTED_BY` has to point at a site that exists and owns
something, checked rather than asserted.

### A member set is not a field contract

Exact POD and an exact member set are the *safe representation* of a document.
They say nothing about what its members mean, and three well-formed documents
proved it: an integer `authority_uuid` issued into an operation signature, a
claim answer naming another participant durably recorded, and a text
`generation` reaching SQLite's INTEGER column **after** the authority had
answered the claim — the worst moment to find out, because the authority holds a
live assignment and the manager has no record.

Twelve injected member entries are now discovered structurally — a member read
on a capability-origin value, followed one level into this module's helpers and
keyed to the crossing rather than to the reading site. Two of an assignment's
four parts are *relationships*: a perfectly well-formed identity naming another
participant or another Work is not this manager's assignment. Those are
compared, not shaped.

### What the machinery caught before a reader did

Two things, and this is the first round where that has happened twice.

A shared owner building its labels from the caller's noun produced a label with
no literal part, and the inventory refused it on the spot. Labels are now
literal-or-template: the fragment is what the source says, the probe asserts the
**full** label — so a probe aimed at the claim answer cannot be satisfied by the
committed claim's refusal.

And driving the generation range turned up a redundancy rather than a missing
case: the frozen bound is already owned by the exact-POD rule that owns the
document the member arrives in. My range check was a second owner for one
property, and unreachable besides. Deleted rather than documented — the third
unreachable boundary this campaign has made me remove.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **473 tests**, all pass on Python 3.13.7;
  the same 473 inside the locked environment.
- Twenty mutations, eighteen witnessed. Two began as zeros and were missing
  cases: a generation past the frozen range (which produced the redundancy
  above) and a record beside a `live` settlement — every settlement case I had
  written used the authority's own `record: None`, so the one path whose whole
  point is that the manager writes nothing had never been handed a decision
  nobody made.
- Two **real equivalences**, left as ones: every constructor exception names a
  site that exists and every probe's fragment is part of its full label, so
  relaxing either assertion changes no verdict. Both mechanisms are proved
  separately by a fabricated violation.
- 18 regressions added (455 → 473), including the reviewer's six retained ones.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of the centralized model and its inventory as one unit.**
Cut D remains unstarted, as the gate requires.


## Three of the four parts are relationships — 2026-08-24

Two P1s, and both are instances of sentences I had already written down.

I made `_assignment` own each part of an assignment identity and compare the two
I had decided were relationships — the Work and the participant. `authority_uuid`
I typed as durable text and left unrelated. So a perfectly well-formed
assignment from authority `ffff…` was accepted for an offer issued from
`0000…a`, advanced it to `claimed`, and recorded the foreign generation. **A
four-part identity is not owned if one of its relationships is only shaped.**

And "a member set is not a field contract" — last review's sentence — was still
true in two places I had not applied it. A retirement's `reason` and
`disposition` were checked for *presence* while the manager records one and
branches on the other, so an integer reason was adopted as the terminal
decision. And `Column.members` was a tuple of names, so a persisted refusal with
an integer category passed the row contract and reached `ContractRefusal`, whose
closed-pairing check is an *assertion* about this build's own raising sites — a
caller replaying its first answer got an `AssertionError`.

### The gap was in the tracking, not in any owner

The universe stopped at `bound = answer.get("record") or {}`, at a private
helper's return, and at a list of rows. Worse: there were **two** tracking
functions and they had drifted — a crossing handed *into* a helper was followed,
the same crossing handed back *out* of one was not. They are one `_source` now,
following every shape to a fixpoint. Adopted origins name the read as well as
the table, and a column that is read is its own entry with its own probe: 29
adopted entries where there were 5.

### The circularity my own fix created

The column probes are generated from the table contracts — but keyed by the
universe, so a change that stopped the tracking seeing columns would shrink
*both* sides and no gate would notice. That is this campaign's finding, arriving
inside my correction of it. So there is a second mechanism that uses none of the
tracking: a flat scan for `x["<name>"]` where the name is a column of a table
this build owns, compared against what the tracking found. Three mutations are
caught by it and by nothing else.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **480 tests**, all pass; the same 480 in
  the locked environment.
- Sixteen mutations, **all witnessed**. Six began as zeros. Three were one
  missing case: every sealed-refusal case I had written spoiled the *category*,
  which the first check catches — so the pairing, the message rule and the
  durable marker had never been driven. Testing the first field of four is not
  testing the contract.
- 7 regressions added (473 → 480), including the reviewer's four retained ones.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of the centralized model and its inventory as one unit.**
Cut D remains unstarted, as the gate requires.


## I used the public name because it was public — 2026-08-24

Two P1s, and both are the same mistake wearing different clothes.

I closed the adopted refusal's pairing against `ERROR_CODES`. That is the
*readable* vocabulary — an ordinary mutable dict a consumer maps onto the wire —
and the contracts layer keeps it deliberately non-authoritative, with its own
case proving a caller may append to it without opening the frozen pairing behind
`ContractRefusal`. So the boundary that adopted persisted refusals was closed
against something that can be widened, while the constructor a line later stayed
closed; the disagreement surfaced as an `AssertionError` to a caller replaying
its first answer.

**I used the public name because it was the public one. What I needed was the
authority, and the two are not the same thing just because one is exported.**
`contracts.errors.is_closed_pair` is that authority now: one shared question over
the private frozen pairing, carrying no mutable state. And it types before it
places — `x in mapping` on a list *raises* rather than answering, so a list
category had been escaping as `TypeError` from the boundary meant to own it. A
check that assumes the type it is checking is not owning the field.

### Two doors into one document, and I fitted a lock to one

PLAN 4cf split public revival from trusted replay, correctly. The next round gave
the **adopted** half a field contract and left the **public** half checking four
member names — so through `revive_refusal` a list category escaped as TypeError,
a cross-category pair as AssertionError, an integer message was accepted into a
refusal, and a `false` durable marker was silently rewritten to true. This
campaign's defect class, arriving inside the correction for it. There is one
`boundaries.sealed` now and both doors call it.

### Caller-domain fields are entries

The inventory confirmed the model gap rather than four local defects: it held
`('caller', 'store.py:revive_refusal', 'sealed')` and nothing about its members.
Injected documents had member entries and adopted rows had column entries — a
caller's structured value had neither, because a parameter was not an *origin*.
It is now, so one rule finds `sealed.category`, `claim.generation` and
`operations.refusal` alike. Three domains, no domain-specific exception, which
is what the last four reviews have each been about.

`sealed.durable` is deliberately not an entry: nothing outside the layer reads
it, and inventing a read to make an entry appear would be the decoration this
file exists to stop.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **483 tests**, all pass; the same 483 in the
  locked environment.
- Ten mutations, **all witnessed, no zeros**. G1 has a single witness — the
  reviewer's own, which widens `ERROR_CODES` and requires the boundary to stay
  shut. That is the honest shape: there is one way to observe "this does not
  consult the widenable value".
- 480 → 483, the reviewer's three retained regressions. No other regressions were
  needed: the corrections were to shared owners and to the universe, not to sites.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of the centralized model and its inventory as one unit.**
Cut D remains unstarted, as the gate requires.


## Cut D, first slice — 2026-08-24

The boundary model was signed off and Cut D released. PLAN 4be covers attempt
axes, activation, cancellation ordering, output freeze, intake and cleanup; this
delivers the first three, in the order the frozen host slices *itself*. What is
absent is named in the module's own docstring: runtime start, reconciliation and
cancellation ordering introduce the injected adapter and agent boundaries, and
what a conforming adapter must *be* is a later item's to pin.

Activation is the piece worth stating plainly: **three things must agree** — the
session's binding, this attempt's own committed claim, and the authority's live
assignment. Any two agreeing is exactly how a foreign session or a replayed
activation gets in, so each case removes one of the three.

### The inventory is load-bearing now

Writing a new module against it was the first real test of that, and it caught
three things before any reader did:

- a shared owner whose label had no literal part — the second time this campaign,
  and the second time the machinery rather than a review said so;
- a blanket rename that ate its own definition (`def __fixed_assignment`), which
  is the exact defect I recorded three cuts ago as "a rename is a refactor and I
  did it as a search-and-replace";
- two unreachable owners over `COALESCE(MAX(x), 0) + 1` — the column is INTEGER
  in a STRICT table and the empty case is the COALESCE. Deleted, not documented.

The universe grew from 148 entries to 194 with no hand-written addition to the
discovery: parameters, capability calls, SQL reads and member reads were all
found by the same rules. What I had to write was owners and probes.

### Mutations

Eighteen run, sixteen witnessed. Two zeros were the same shape — **a guard one
process cannot reach on its own** — and are now driven the way they actually
happen: a store written before the unique index, and a trigger another build
could have put on the observations table. A guard that can only be reasoned
about is a guard nobody has checked.

**H14 is a measured equivalence and the measurement is the finding.** I wrote the
case expecting activation's compare-and-swap to refuse a racing second manager,
and it does not: both derive the same operation identity, so the journal replays
the first committed answer before the second act runs. I kept the swap and am
flagging it as a judgement call rather than a proof — unlike the five unreachable
*validations* this campaign has made me delete, it is the write's own condition.

### An instrument failure

The first mutation run hit a ten-minute execution cap and was killed **between**
writing a mutant and restoring the original, leaving `attempts.py` mutated and
the next run's baseline dirty. A fourth instrument-failure shape after the false
zero, the false non-zero and the stale bytecode. The restore is in a `finally`
now, the run moved off the capped path, and the discarded results are not
reported. The tree was repaired by rewriting the text, not by a Git operation.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **514 tests**, all pass; the same 514 in the
  locked environment. 483 → 514.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting independent review of Cut D's first slice.** The next slice is runtime
start, reconciliation and cancellation ordering.


## Three rules I had already written down — 2026-08-24

Three P1s on Cut D's first slice, and each is a rule this dossier already
contains that I did not carry into the new module. That is worth saying plainly:
the boundary model is mechanical now and catches a missing *owner*, but it does
not catch a rule I know and did not apply.

**The journal answers first.** `activate_assignment` returned from its
already-fixed branch before reaching the journal, so the first call committed
`already_fixed=False`, a later exact retry synthesized `True` from the row, and a
contender that had read before the commit replayed the journalled `False`. One
act, two answers, chosen by when the retry arrived. The order of the three checks
is now deliberate: the fixed-assignment *mismatch* first, because it is a
precondition about the attempt and deserves a diagnostic naming what differs;
then the journal, with full-signature collision intact; then the already-fixed
fallback, which now means what it always should have — an attempt found fixed
with no act of this build's to reproduce.

**A closed set types before it asks.** `axis not in TRANSITIONS` was asked of the
raw operand, so a list escaped as a raw `TypeError` while the inventory declared
it owned. This is the same defect PLAN 4cj corrected for the sealed pairing *one
round earlier*, in code I wrote after that correction.

**Only contention is translated** — by SQLite's own result code, never by prose,
with the primary code masked out of the extended one. A locked database at this
boundary means one thing: another writer is deciding this attempt. Everything
else keeps its identity, because a caller told to retry a constraint violation
retries it forever.

### Mutations

Nine run, **all witnessed**. J8 began as a zero and was a missing case of a shape
the frozen host had already recorded as its own P2: every failure I had driven
differed in result code *and* in wording, so matching on prose passed
everything. The witness is a trigger raising `busy provider invariant: database
is locked by policy` — application-controlled text that says "locked" and is a
constraint violation.

### The ruling I asked for

The review confirmed the activation compare-and-swap stays: H14 is a legitimate
measured equivalence through today's single public operation identity, and that
does not make the write's own condition redundant.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **518 tests**, all pass; the same 518 in the
  locked environment. 514 → 518.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review of Cut D's first slice.** Runtime start, reconciliation and
cancellation ordering remain unstarted.


## Cut D, second slice: fence, then stop — 2026-08-24

The rest of the frozen `attempts.mjs`, and the ordering *is* the content. The
start operation is journalled before the adapter is called, because an axis
label is not an effectively-once act. Reconciliation decides by identity **and**
by the full labels, with the minted runtime checked *before* the filter — one
carrying another assignment's labels is not absent, it is wrong, and this call
caused it. Cancellation fences at the authority first: until the generation is
fenced the assignment is still live, so a runtime stopped first would be a worker
torn out from under an assignment the authority still believes is executing.

Two injected capabilities enter — the runtime adapter and the provider agent.
Positive runtime absence still cannot be proven, so the retry path stays closed
and says so.

### Two deliberate departures from the oracle

Both reported rather than quietly made. The cancellation answer is **nested**
rather than merged: a document whose member set depends on the branch that built
it cannot be owned at the far end. And the lost-race catch is **narrowed** to the
compare-and-swap's own refusal, because the oracle's broad catch swallows an
operation collision and answers it as a cancellation.

### What the inventory found

Making the adapter and agent capabilities surfaced a modelling gap I had to fix
rather than declare: `cancel` exists on the authority session *and* on the
provider agent, so a member name alone stopped identifying a crossing. For those
two the holder's name is now part of the member's identity — two crossings that
share a verb are still two crossings.

### Mutations

Seventeen run, fifteen witnessed. **K6 was a redundant check and is gone**: an
early mismatch test in `_attach` changed no verdict, because the compare-and-swap
refuses that case and the lost path answers the same cancellation from a *fresher*
read. Sixth duplicate of a write's own condition removed.

**K17 is a measured equivalence whose value is that it makes K7 observable.** The
narrowed catch has nothing to catch today; what it does is turn a wrong operation
identity from silent into visible — K7 measures zero under the oracle's broad
catch and one under the narrow one. I am reporting it as idle rather than as
proved.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **541 tests**, all pass; the same 541 in the
  locked environment. 518 → 541.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting independent review of Cut D's second slice.** Output freeze, intake
and cleanup remain unstarted.


## An effect outside the transaction is not part of the act — 2026-08-24

Two P1s on Cut D's second slice.

`_attach` committed the runtime identity and the operation result, and *then*
observed `running`. A fault between them left a committed attachment whose exact
retry replayed the recorded answer without running the action — so it answered
`attached` forever while the durable axis still said `start-requested`.
Effectively-once means the retry reproduces the first act's **whole** effect, and
an effect outside the transaction is not part of it. The observation is inside
the journalled transaction now, which is what its savepoint was built for.

**I changed two lines of a retained reviewer test, and I am flagging it rather
than burying it.** The review offered two remedies and recommended this one;
under it the crash commits *nothing*, so the premise assertions — that the
attachment is committed and the axis unmoved — describe a state the fix makes
impossible. Those two now assert what atomicity produces; everything after the
store close/reopen is exactly as written. If the reviewer prefers the other
remedy (a committed attachment a later replay heals), I'll implement that
instead — the choice isn't mine to assume.

And a fence for another generation is not this cancellation: the port related
the authority, the Work and the participant and left the **generation** only
shape-checked, so a fence of generation 2 was accepted for an attempt expecting
generation 1 — and both downstream boundaries were then ordered with no evidence
that this attempt's generation had been fenced. All four members are compared
now.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **543 tests**, all pass; the same 543 in the
  locked environment. 541 → 543.
- Three mutations, all witnessed — including one that relates three members and
  not the fourth, which is the finding's own shape.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review.** Output freeze, intake and cleanup remain unstarted.


## The output slice decomposes further than the plan item reads — 2026-08-24

Cut D's remaining work was unblocked, and revalidating it against the tree
changed my plan — which is what the revalidation is for. Output freeze is not one
transition: `output.mjs` depends on `manifests.mjs` for retention, on three
tables this store does not have, and on `validateManifest`, which in the frozen
host is not a schema call but **eight distinct §12 rules** over the document.

So this round delivers the two rules that are about the document *alone*:
`validate_fragment`, which reads the frozen schema at a **definition** rather
than at the envelope, and `verify_manifest_digest`, §12's identity rule. I did
not name it `validate_manifest`: delivering half a rule under the name of the
whole is the floor-versus-contract mistake already recorded here. What remains is
named in the evidence rather than implied.

**Two decisions worth a ruling.** A definition is a *name*, never a subschema —
the frozen host accepts an inline fragment and this does not, because a
caller-supplied subschema is a program this boundary would compile and run: the
same seam `validate_against`'s identity check closes, arriving as data instead of
as an object. And the fragment subschema is `{$schema, $id, $defs, $ref}` and
nothing else, because keeping the envelope's `oneOf` would make every fragment
have to be an envelope to validate as itself.

### Mutations

Eight run, seven witnessed. **M4 began as a zero and the reason is worth
keeping**: my first case for it was a *refusal* — an empty document rejected as
an `inputManifest` — and that proves nothing, because a fragment held to the
envelope is refused too, for a reason nobody reading the message would notice.
The positive case is the one that says it. A refusal is not evidence that the
right rule refused.

**M5 is a real equivalence and stays one.** Once the declared digest is verified
it equals the recomputed one; what recomputation buys is *provenance*, which the
frozen host says of its own equivalent line.

**An instrument note:** M5's first run reported one failing test — a threaded
store case with nothing to do with digests. Alone it passes three times, so that
was timing noise, not a witness. A false non-zero, the second of that shape here;
I checked rather than banked it.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **555 tests**, all pass; the same 555 in the
  locked environment. 543 → 555.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting independent review.** Next: the rest of §12's manifest rules, then
retention and the outputs tables, then freeze and record.


## Testing the first clause four times is not testing the rule — 2026-08-24

§12's manifest semantics: a Work id carrying its authority's prefix, locators
that are absolute and readable and carry no query or fragment, content manifests
whose entries are sorted bytewise and unique and whose declared count, byte total
and tree digest all recompute, and an input manifest's unique names,
non-overlapping destinations and single object namespace.

Still **not** the whole §12 trust entry, and named so. §13's durable-secret rule
is absent because its second half needs a reference-counted live-bearer registry
this distribution doesn't have, and shipping the member-name half under the whole
rule's name is the floor-versus-contract mistake already recorded here.

### Two more unreachable boundaries

The seventh and eighth. Every path member of a manifest is typed `relativePath`,
whose pattern already refuses what `check_relative_path` refuses; and
`assignmentRef.generation` already carries `minimum: 1`. Both deleted from the
composite — but **neither reliance is left implicit**: a case pins each of the
schema's own guarantees, so if either ever stops, the gate says so rather than a
document getting through.

### Mutations

Seventeen run, all witnessed. Five began as zeros, and **four were one missing
case with one cause**: every URI case I had written spoiled the same clause, so
the fragment, the relative locator and the unreadable one were never driven. A
rule with four clauses needs four cases.

The fifth had a different cause worth keeping: the published conformance vector
carries a *directory* source, so the versioned-source branch had nothing to drive
it. The case now builds that source from the schema's own required members rather
than from a vector that does not exist.

**The vector is the baseline.** Every case spoils exactly one thing in the
conformance vector the worker-contract finding published, and reseals it so the
identity rule doesn't refuse it before the rule under test is reached. A manifest
I wrote by hand would be a document built to pass my own rules.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **567 tests**, all pass; the same 567 in the
  locked environment. 555 → 567.
- One declared widening: `urllib` joins the standard-library allowlist for §12
  rule 4. No runtime dependency added.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting independent review.** Next: §13's durable-secret rule with the
registry it needs, then retention and the outputs tables, then freeze and record.


## A successful split is not a parse — 2026-08-24

`check_uri` ran `urlsplit` inside a `try` and threw the result away, so the only
thing it proved was that the splitter did not raise. `urlsplit` is deliberately
permissive: it hands back a hostname containing a space, a port that is not a
number, and userinfo without objecting — so `worker:secret@host`, a credential
in a durable locator and the exact thing §12 rule 4 exists to keep out, was
accepted. The split's *answer* is read now.

And an exported rule owns its own operand. `check_work_ref` and
`check_content_manifest` are public and indexed their arguments as though the
composite had already schema-owned them, so a direct caller's malformed value
escaped as a `TypeError`, and a dict *subclass* executed hostile `__getitem__`
inside the trusted contracts layer. One public wrapper that validates, one
private body the composite calls with values it already owns.

### Mutations

Seven run, all witnessed; two began as zeros.

**P2 is the same shape as last round's URI zeros, one round later.** My case
supplied *both* halves of the userinfo, so dropping the user-name half changed
no verdict — the rule was proved by a locator that would have been refused
either way. Half a check passes a test written against the whole, and I have now
made that mistake twice in the same function.

**P7 is structural and needed a structural check.** Putting the public wrapper
back inside the composite validates one document twice; both orders accept and
refuse exactly the same inputs, so no behavioural case can see it. The witness
reads the composite's own AST — the mechanism the manager's inventory uses one
layer down.

Worth naming: 4bz's "not owned twice" rule has been enforced by that inventory
since it was written, and the **contracts package is not in it**. This is the
first double validation the inventory could not have caught, and a review caught
it instead.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **573 tests**, all pass; the same 573 in the
  locked environment. 567 → 573.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review.** Next: §13's durable-secret rule with the registry it
needs, then retention and the outputs tables, then freeze and record.


## Measured rather than reasoned about — 2026-08-24

`check_uri` ran its authority and port rules only when the split found a
non-empty netloc, so `https://` returned unexamined while the frozen host's
constructor throws for it. The clause is guarded by the **scheme** now, not by
the netloc.

The obvious rule — "an empty authority is invalid" — is wrong, and I checked
before writing it. Against the frozen constructor: `https://` and `http://`
throw; `file://`, `file:///x`, `artifact://`, `foo://`, `urn:x:y` and
`mailto:a@b` all succeed with an empty host. So the rule is that the schemes
which *require* a host must have one, and the list is that measurement rather
than a policy I invented. `file://` staying valid matters: it's a form the
contract uses, and a rule refusing every empty authority would have refused it
while looking stricter.

Three mutations, all witnessed. The one worth having is "every scheme requires a
host" — the rule I would have written without measuring — and what catches it is
the list of forms the frozen constructor accepts.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **574 tests**, all pass; the same 574 in the
  locked environment. 573 → 574.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review.** The review's prevention decision is accepted and queued
as the next slice: a contracts-package anti-loop inventory, before §13.
Retention, the outputs tables and freeze/record stay behind both.


## The mutant was right — 2026-08-24

My last correction was half a correction. It asked `urlsplit` for `netloc` and
then applied a measured scheme list, which composes two facts from **different
parser models**. The frozen reader normalizes `https:x`, `https:/x` and
`https:///x` all to `https://x/` with host `x`; Python reports an empty netloc
for each, so three accepted forms were refused as hostless. And the negative side
was worse: `https:worker@example.test` carries a credential the frozen reader
sees plainly, and my rule reported "no host" and never reached the userinfo
check. A remedy that merely accepted the shorthand forms would have reopened that
boundary while looking like a fix.

The authority of a host-requiring scheme is now derived the way the frozen reader
derives it, and every form is measured rather than reasoned about.

### A fourth answer for a zero

I wrote the port split as "everything after the **last** colon". A mutation to
the first colon changed no verdict — so I measured both against the frozen
constructor and found **my version wrong**: `https://a:b:8080/x` throws there,
and my rule accepted it with port 8080. Taking the last colon quietly reads a
malformed authority as a well-formed one, which is the same class of
disagreement the whole correction exists to remove.

The rule I've been applying to a zero-scoring mutation — *missing case, redundant
code, or real equivalence* — has a fourth answer: **the mutant is right**. This
is the first time in this campaign that has happened, and I would not have found
it by reading.

### Mutations

Nine run, all witnessed; three began as zeros. R8 needed an IPv6 literal
*without* a port, since with one both spellings agree; R9 needed a userinfo case
on a *non*-special scheme, because every credential case I had written used a
special one.

### Verification

- `XDG_RUNTIME_DIR=/tmp just gate` — **580 tests**, all pass; the same 580 in the
  locked environment. 574 → 580.
- Zero temp roots; frozen Node oracle untouched; whitespace clean.

### State

**Awaiting re-review.** The contracts-package anti-loop inventory remains the
next slice; §13 and retention stay behind it.


## Blocked on a ruling, and the measurement that should decide it — 2026-08-24

The review requires the URI parser-equivalence strategy pinned before the next
implementation edit. I made none. Source is red by the review's own design — its
nine additive methods — and all 580 delivered tests pass.

**The frozen constructor normalizes.** I measured what it *does* with the forms
it accepts, not only whether it accepts them: ten of nineteen come back as a
different string — uppercase hosts lowercased, non-ASCII punycoded,
percent-escapes decoded, leading-zero ports trimmed, empty port markers dropped,
and the shorthand slash forms rewritten.

So "accept exactly what the frozen reader accepts" **cannot be a rule over the
original text** — and this module's own §12 rule 4 comment says the opposite
about how these rules must work: the rule is read off the original text, because
a durable string's meaning must not be decided by a parser's reconstruction of
it. A locator whose meaning depends on a normalizing parser is one two conforming
readers can disagree about, which is the failure §3.3 exists to prevent. That
isn't a preference; it's the same defect class the last three reviews have been
finding one edge at a time.

### What I recommend

**Strategy 2** — one smaller canonical grammar both runtimes enforce, with no
normalization anywhere in it. The grammar and its full supersession list are in
the evidence. The row I want the reviewer to look at hardest is the shorthand
slash forms, because the last two reviews had me *add* support for them; under
this grammar a producer must write the canonical two-slash form. That is a real
change to accepted input, which is why it needs a ruling rather than my
judgement.

Strategy 1 would need WHATWG host parsing, percent-decoding, IDNA and port
normalization — `urllib` does none of them — so a second runtime dependency,
reopening 4bh. It also cannot be verified here: the index has been unreachable by
DNS for several rounds, and I won't claim a package exists or resolves offline
without measuring it.

### State

**Blocked on the ruling.** I have not edited `check_uri` and will not until the
strategy is pinned — three rounds of chasing edges is the anti-loop signal this
dossier already knows how to answer, and the answer is not a fourth round of the
same.


## One grammar, two runtimes, one list — 2026-08-24

The ruling landed: v12 will not reproduce the frozen constructor's WHATWG
acceptance surface. Both runtimes enforce one smaller, shared, versioned grammar
instead, and `v12/fixtures/uri-vectors.json` — 20 accepted forms and 50 refused,
each with its reason — is the authority for both. Not two implementations that
agree today: one list, read by both suites.

Every clause is checked on the original text with no parse and no
reconstruction. The IPv6 literal is the one place a library decides, and both
sides additionally require it to be lower case and to come back as the *same
text*, because an address that only becomes valid after normalization is not
canonical.

`urllib` leaves the Python allowlist and `ipaddress` joins it. The grammar needs
no URI parser at all now — a smaller surface than the widening I asked for two
rounds ago.

### Every superseded assertion, named

The ruling requires these recorded rather than quietly deleted.

**Python, `ExportedSemanticRulesOwnTheirCallers`:**
- `test_the_frozen_reader_decides_where_the_authority_starts` — required
  `https:x`, `https:/x`, `https:///x`, `https:x:8080/p` **accepted**. Shorthand
  is excluded; all four now refuse.
- `test_the_frozen_constructor_not_urlsplit_decides_the_host` — same forms, same
  supersession.
- `test_an_empty_port_is_not_an_invalid_port` — required `https:x:`,
  `https://x:`, `artifact://x:` accepted. Empty markers excluded.
- `test_the_scheme_decides_whether_a_host_is_required` — accepted `file://`,
  `artifact://`, `urn:x:y`, `mailto:a@b`. Non-file schemes need a non-empty
  authority, `file` needs a path, opaque forms are excluded.
- `test_a_credential_is_found_wherever_the_authority_starts` and
  `test_special_scheme_normalization_does_not_hide_userinfo` — expected the
  shorthand credential forms to refuse *with the userinfo reason*. They refuse at
  canonical syntax first, which the ruling permits; the refusals are retained.

**Python, `TheCanonicalVectorIsTheBaseline`:**
- `test_a_source_uri_is_absolute_readable_and_bare` — three expected phrases
  changed to the grammar's more precise reasons. Every refusal retained.

**Node, `worker_manager_contracts.test.mjs`:**
- "a durable locator carrying a credential is refused" — two phrases changed
  from `/absolute/` to `/canonical locator/`.
- "a URI this build cannot parse is refused, opaque forms are not" — **renamed**
  to "a URI outside the canonical grammar is refused". Its premise was that
  opaque forms stay accepted because refusing a parse failure "costs the contract
  nothing"; the ruling supersedes that, and `urn:` and `mailto:` move to the
  refused list.
- "a malformed locator cannot reach the trusted manifest" — `/parseable/` became
  `/does not close it/`.

Retained unchanged on both sides, with a case asserting the corpus still carries
each: query, fragment, canonical userinfo, malformed authority, empty host, and
every port refusal.

### Verification

- Python: `just gate` — **574 tests**, all pass; the same 574 in the locked
  environment. Zero temp roots.
- Node: the three locator cases and the new shared-vector case pass.

**An operational finding, reported rather than fixed or hidden.** The frozen
prototype's own Node suite has three failures that are not mine and that this
edit does not touch — all about refusal *message length*, one reporting a
269,042-character refusal for a 20,000-member capability envelope, and none of
them calling `validateUri`. I checked that my edit lost no export (39, none
missing) and touched no shared helper. They are outside this boundary and outside
W4's scope, so I have not changed them: silently repairing somebody else's
failing gate would misreport what this round did.

### State

**Awaiting independent review of both runtimes.** The contracts-package
anti-loop inventory is next, then §13, then retention.


## The address family with no agreed spelling — 2026-08-24

The reviewer's two P1s were right and small: Python was asking `ipaddress`
whether the literal PARSED, which says nothing about whether the text is the one
spelling this grammar admits, and neither runtime bounded DNS length, so a
64-byte label was a durable locator. Both are fixed in both runtimes, and 253
exactly is accepted where 254 is refused.

Implementing the first one exactly as prescribed would have left a
disagreement. The prescribed alphabet `[0-9a-f:.]` admits the dot, and a
differential sweep — not a vector — turned up this:

```
https://[::ffff:1.2.3.4]/x    python ACCEPTS   node REFUSES
https://[::ffff:102:304]/x    python REFUSES   node ACCEPTS
```

For the IPv4-mapped range `::ffff:0:0/96` the two libraries' canonical spellings
are *each other's refusals*: `ipaddress` writes the dotted form and returns it
unchanged, the frozen constructor writes the hex form and rewrites the dotted
one. There is no text for a mapped address both runtimes accept, so "canonical
text" cannot be satisfied by both at once and a locator one runtime wrote would
be unreadable to the other — the §3.3 failure this whole ruling exists to
prevent.

So the family is **excluded**, in both runtimes, alongside shorthand and the
opaque forms; admitting it later is a versioned contract change. The alphabet is
`[0-9a-f:]` with no dot, which is a narrowing of what the review asked for, and
it is named rather than slipped in. The exclusion is the mapped *range* and not
everything shaped like it — `::ffff:1` is `0:0:0:0:0:0:ffff:1` and stays
accepted.

### Evidence the corpus cannot give

| sweep | population | python accepts | node accepts | disagreements |
|---|---|---|---|---|
| general locators | 1,532 | 178 | 178 | **0** |
| IPv6 spellings | 10,162 | 521 | 521 | **0** |

The IPv6 sweep is every zero-run compression, zero padding, upper case and
dotted tail of some 900 addresses. Before the exclusion these same sweeps
reported three disagreements, all of them the mapped family.

### Mutation: 18 of 20 killed, and the two survivors are the report

Killed: every DNS bound (removed and off-by-one, both runtimes), the Python
alphabet (removed, widened to the dot, widened to the scope), the canonical-text
rule (removed in both, and inverted), the mapped exclusion (removed in both,
narrowed to the dotted form in both, and loosened to a bare `::ffff:` prefix).

**Survived:** deleting the Node alphabet clause, and widening it to admit the
dot. That constructor already refuses every literal the clause would catch —
measured with a probe over every ASCII character outside the alphabet in
seventeen positions, which round-trips nothing unchanged.

The clause is kept, and the distinction is the whole point. The boundaries this
campaign has deleted were unreachable *by construction*. This one is unreachable
because of what a **third-party normalizer does in this runtime version**, and
that normalizer's acceptance surface is exactly what the ruling refused to treat
as a contract. It is the only clause there that fixes the grammar without asking
it. Its assumption is now pinned by its own case, so a runtime that starts
round-tripping a scope id fails a test that names the clause, rather than
quietly widening what a durable locator may say.

Two clauses were **deleted as measured redundant**: the lower-case check in both
runtimes, which the alphabet subsumes entirely.

### Verification

- Python: `just gate` — **577 tests**, all pass; the same 577 in the locked
  build. Zero temp roots.
- Node: `npm test` — 691 tests, 688 pass. The three pre-existing message-length
  failures reported last round are unchanged and untouched.
- Corpus: 20 accepted, 58 refused — four vectors the reviewer added, four this
  correction added.

### State

**Awaiting independent review of this correction.** Contracts inventory, §13 and
retention stay unstarted, as the review directs.
