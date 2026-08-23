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
