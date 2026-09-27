# Implementer progress — W275775 (Child B)

Kept by baton.claude. Each entry records what was measured, not what was intended.

## 2026-09-27 claim 281291 — the renewal act, and the arbitration it had to move

Dossier created and bound at revision 1 (bind 281312) before any edit, per owner brief 275775.
Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     adea8046a8f9   PRODUCT, exclusive custody
    v12/python/tests/manager/test_boundary_inventory.py   10b1851d3ff0   entry declarations only
    v12/python/tests/manager/test_dependencies.py         b3a218f09688   operand declarations only
    work/.../finding-v12-token-renewal/test_renewal_arbitration.py  032b2f6fc4a2   NEW selector

### What I found before editing

`RENEWAL_LIMIT = 4` was declared, with its semantics recorded beside it, and **nothing
consumed it**. There was no renewal act at all, so every deadline reader answered the
ACQUISITION's own `expires_at`. That is why this Work is arbitration and not one new
function: a renewal that did not move what `token_of`, `_owning`, `revoke` and the conflict
message read would have granted nothing.

### The act

`renew(control, token, *, execution, operation, expected_revision, seconds=LIFETIME_SECONDS)`.

* **One record per REVISION**, `resource-token.renewed:<domain>:<generation>:<revision>`.
  A single per-generation identity would have had to choose between being replayable and
  being non-repeatable; the revision in the identity gives both.
* **`expected_revision` is the condition.** Revision 0 is the acquisition. A caller naming
  a committed revision replays it — that is the lost-reply case, and it extends nothing. A
  caller naming a revision past the next one is refused: a renewal cannot skip the state it
  claims to have observed.
* **The signature covers the REQUEST, not the clock.** Child A's review 13:41:00Z found
  `returned` stamping a fresh clock value into its signed operands so that an exact replay
  changed its own signature. I hit exactly that here — the lost-reply case failed with a
  collision — and applied the same correction rather than rediscovering it: the instant and
  the deadline ride the recorded document, not the signature.
* **The deadline is composed outside the lock**, where `acquire` composes its own and for
  the same recorded DB-1 reason; the CONDITIONS (owner, lifecycle, current deadline,
  revision) are all re-proved inside the write, so the serialization loses nothing.
* **Refuses** expired, revoked, returned, cross-execution, cross-operation, forged owner,
  skipped revision, and exhaustion — and exhaustion **holds**: the refusal leaves the
  resource outstanding and a competitor still excluded, which is what `RENEWAL_LIMIT`'s
  recorded semantics say.

### The arbitration

`token_of` now composes the effective state from the committed renewals: `expires_at` is the
last renewal's, `acquired_expires_at` keeps the original grant for a reconciling restart,
and `revision`/`renewals`/`renewals_remaining` are answered beside them. `_deadline_of` is
the ONE derivation, and `_owning` and the conflict message read it — so "renewal and expiry
compete against that same current state" is a property of one function rather than an
agreement between four readers.

### Measured

* New selector `test_renewal_arbitration.py`: **18 PASS 0.049s**, standalone, covering every
  clause of the section 17 renewal row — recorded once, no writer or other row moved,
  per-revision records to the bound, replay/lost reply, changed-operand collision, skipped
  revision, expired/revoked/returned/cross-execution/cross-operation/forged-owner refusals,
  the stale-expiry-versus-renewed-deadline arbitration in both directions, exhaustion
  holding, and two managers racing one revision into exactly one extension.
* Child A's ten accepted selectors: **all PASS** unchanged.
* `test_intake`, `test_attempts`, `test_workspaces`, `test_single_worker`, `test_tool`,
  `test_review_cycles`, `test_recovery`: **all PASS**.
* Catalogs: `test_boundary_inventory` **26 failures with the failure name-set byte-identical**
  to Child A's accepted baseline, and `tokens.py` still at **0 unowned** — the four new
  `renew` entries are declared (store stated, the two document members stated with the
  existing re-read witness, `seconds` delegated to its own expiry boundary).
  `test_dependencies` **73**, unchanged, with `expected_revision` declared.

### Two measurements that corrected my own assumptions

1. A renewal at the same instant with the same lifetime records a revision and **gains no
   time** — the deadline is `now + seconds` on the host's clock. My first case assumed the
   deadline always moves; it is now two cases that state the property and its complement
   (a longer requested lifetime does move it).
2. A revocation racing a renewal is refused in BOTH interleavings under a deterministic
   clock, so a concurrent case cannot distinguish which state the loser read: my first cut
   asserted the loser's message named the renewed deadline and it named the acquisition's.
   The expiry-versus-renewal arbitration point is inherently after a renewal commits, which
   the sequential stale-observation case proves; the concurrent case now covers what
   concurrency actually risks, a double extension.

### Remaining

1. No production consumer calls `renew` yet: the owner brief excludes consumer migration,
   so the act and its arbitration stand alone until a consumer is pinned. This is stated as
   a gap rather than implied to be complete.
2. Host-clock competition across a RESTART (TOK-9's "never reuse a monotonic timestamp
   across boots") is not yet exercised for renewal specifically.
3. Renewal against Job execution limits: proved here as "no other row moves", not yet
   against a real Job limit consumer.

## 2026-09-27 claim 281398 — C1, C2, C3 and C4 corrected and proved

Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     207bcf1786e0   PRODUCT
    v12/python/tests/manager/test_boundary_inventory.py   dc2d1fc575ec   declarations, witness
    v12/python/tests/manager/test_dependencies.py         b3a218f09688   unchanged this claim
    work/.../test_renewal_arbitration.py                  d0f0b0b83a25   selector, 35 cases

Both reviewer probe cases reproduced first: `review_renewal_edges_20260927.py` gave 1 error
and 1 failure exactly as the review said.

### C1 — a judged expiry is a record, not arithmetic

`_owning` compared the wall clock with the deadline, so the probe's sequence -- observe
expired, be refused, move the same clock back, ask again -- renewed a token expiry had
already won. TOK-9 forbids that ("no heartbeat, late renewal request or clock adjustment
revives the token") and says ambiguous timing holds.

`EXPIRED_KIND` records the judgement. `renew` MAKES it: when `_owning` refuses for expiry,
the judgement commits in its own short write before the refusal propagates, so a caller that
never sees the answer still cannot revive the token. `_owning` consults the record first --
it cannot be un-made -- and `token_of` answers `expired` stickily with `expiry_judged_at`
beside it, because a reader that contradicts an authoritative decision is how a caller talks
itself into reviving one. A second judgement REPLAYS the first, so the recorded instant is
the moment expiry won rather than the latest notice.

**It frees nothing.** Proved, not asserted: the resource stays outstanding, a competitor is
still excluded, and the revocation path is still open -- which is the only way a held
resource is ever reclaimed. A renewed generation is judged against its RENEWED deadline, so
the fence follows the arbitration rather than the original grant.

**Reviewer's P1 probe now passes** (`test_clock_rollback_cannot_revive_observed_expiry` ok).

### C2 — the bound never hides a committed renewal

The exhaustion refusal ran before the journal could answer a request whose record already
existed, so the one unrecoverable lost reply was the last one -- granting LESS than the
committed state rather than nothing beyond it. The bound now applies only to a NEW extension
(`revision == len(standing)`), a replay goes straight to `transact`, and the bound is
re-proved INSIDE the write where it cannot be stale. Four cases: final-allowed lost reply
replays without extending, every earlier revision still replays at exhaustion, a changed
operand at a committed revision is a COLLISION rather than a policy denial (so the caller
learns which rule stopped it), and an actual fifth extension is denied with the resource
still held.

**One choice stated rather than discovered:** a replay arriving AFTER expiry is refused as
expired, not answered. The uniform gate is what makes "an expired generation authorizes
nothing further" true without exceptions, and the caller learns the fact that now matters.
Its own case says so.

### C3 — one revision convention

`expected_revision` IS `token_of(...)["revision"]`: the number of committed renewals. An
unrenewed generation stands at 0 and its first renewal names 0. The old code required a
positive integer through `boundaries.generation`, so the obvious caller was refused on its
first call -- and `boundaries.generation` was simply the wrong owner. A local typed check
(`_observed_revision`) owns it: exactly a whole number, zero included, and `True` excluded
by type identity because it is an `int` that would otherwise read as revision 1. Cases:
reader-to-renew round trip at every revision, a revision past the state refused as a skip,
and six malformed shapes refused before anything is decided.

### C4 — the two proofs that were overstated

**Job limits, now populated and read by the real reader.** A real `JobStore` with EXPLICIT
non-default ceilings, submitted through `submit`, read back through
`job_manager.submission.boundary_seconds`. After the full renewal allowance is spent: not one
write in the Job store, the same ceilings, and the limits row unchanged. A second case states
the separation -- an exhausted renewal allowance is not a Job budget, so the Job's
per-invocation ceilings are untouched by it.

Two measurements corrected this case while I wrote it: the shared fixture composes submission
`/1` and `execution_limits` is optional only on `/2`, and the accepted setting names are the
owner's (`provider_turn_seconds`, `verification_command_seconds`), not the boundary names a
reader asks by. Both are recorded at the code.

**The scheduled two-handle arbitration, both directions.** The winner is held inside its own
write transaction while the loser's act is issued on a second handle, so SQLite's write lock
makes the order certain:

* the renewal holds the lock and commits; the revocation then refuses "is not overdue" AND
  its message names the RENEWED deadline -- the arbitration decided it, not the ordering;
* the revocation holds the lock and commits; the renewal then refuses, and no renewal exists.

**A measurement that corrected my own case twice.** My first version took `BEGIN IMMEDIATE`
on the competitor's own connection and ran a production act on it: `cannot start a
transaction within a transaction`, because every act here takes its own. My second counted
calls to place the pause and put it on the PRE-transaction read, so the competitor never
blocked, read the pre-renewal state and refused against the ORIGINAL deadline -- the case
looked like a race and was not one. The pause is now taken only while
`control._connection.in_transaction`, asked of the connection rather than counted.

### Measured

* `test_renewal_arbitration.py`: **35 PASS 0.117s** standalone.
* Reviewer's `review_renewal_edges_20260927.py`: P1 case **ok**; P2 case still errors, and
  the reason is the convention change C3 required -- its loop sends `expected_revision`
  1..4 for a generation standing at 0, which is the OLD off-by-one. Its PROPERTY is proved by
  the four C2 cases above. The probe is the reviewer's artifact and I have not edited it;
  the exact line is `for revision in range(1, tokens.RENEWAL_LIMIT + 1)`.
* Child A's ten accepted selectors: **all PASS**.
* `test_intake`, `test_attempts`, `test_single_worker`, `test_tool`, `test_recovery`,
  `test_review_cycles`: **all PASS**.
* `test_boundary_inventory`: **26 failures, name-set byte-identical** to Child A's accepted
  baseline, `tokens.py` **0 unowned**; the revision operand is stated with a new witness that
  requires both halves (zero accepted and renewing, malformed refused). One redundant
  delegation I had added was removed after `test_no_entry_is_owned_twice` caught it: hoisting
  the deadline composition made the entry layer-owned, so the delegation owned it twice.
* `test_dependencies`: **73, name-set unchanged** and pre-existing.

### Remaining

1. C5, the reviewer's final bounded candidate/path/digest/evidence review.
2. Still true and still stated: no production consumer calls `renew`, because the brief
   excludes consumer migration.

## 2026-09-27 claim 281525 — C1 again: the judgement is now a decision under the lock

Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     8058324e49c9   PRODUCT
    v12/python/tests/manager/test_boundary_inventory.py   ddb3bf093e79   declarations
    work/.../test_renewal_arbitration.py                  b8d85b151196   selector, 38 cases

Reproduced `review_stale_expiry_judgement_20260927.py` first: **1 FAIL**, exactly the race the
review describes. My own fix from the previous claim was the defect: `_judge_expired` took the
deadline and the instant as OPERANDS and wrote unconditionally, so a caller holding an old
deadline invalidated a renewal that had committed while it was paused -- with no clock
rollback anywhere.

### The correction

`_judge_expired(control, domain, generation)` no longer takes what it is judging. Everything
the decision rests on -- the acquisition, the committed renewals, the deadline they imply and
the instant -- is read INSIDE the same short transaction that writes:

* if the generation is NOT expired at that moment, the transaction refuses, `transact` rolls
  back, nothing is written, and the helper answers `None`. A stale caller's refusal stays its
  own business and never becomes a durable fact about somebody else's renewal.
* what IS recorded now names the deadline it judged AND the revision that deadline came from,
  so a reader can see which state expiry won against rather than only that it did.
* a second judgement still replays the first, so the recorded instant remains the moment
  expiry actually won.

### Two things the review asked to stop doing, and both are gone

**No message matching.** The previous cut inspected the refusal text for "expired at" before
judging, which made a durable authority fact depend on prose. It is unnecessary once the
condition lives inside the write: `_judging` simply asks after ANY refusal, and nothing is
written unless the generation really is expired.

**Equivalent semantics wherever expiry is discovered.** `renew`'s body moved into `_extended`
so the judgement wraps the WHOLE attempt. Expiry found in the preflight and expiry found by
the in-transaction re-proof now behave identically: the failed transaction rolls back and the
judgement is then attempted in its own short write -- never nested inside the transaction that
failed, and never a lock held across anything external.

**And the prose the review flagged is corrected** rather than left contradicting the code:
`renew`'s docstring now says the refusal itself is not journalled while the expiry it
discovered is recorded conditionally, and that the record changes only whether the timing fact
can be argued with.

### Three new cases

* the reviewer's exact stale-deadline schedule, as this Work's own case;
* expiry first discovered INSIDE the transaction: the clock passes the deadline while the
  renewal holds the write lock, the rolled-back attempt leaves no renewal, and the durable
  judgement survives the rollback;
* the record names which state lost -- deadline, revision and the observed instant.

### Measured

* `test_renewal_arbitration.py`: **38 PASS 0.129s** (35 preserved, 3 added).
* `review_stale_expiry_judgement_20260927.py`: **OK**.
* `review_renewal_edges_20260927.py`: still 1 error, unchanged and for the unchanged reason --
  its one-based loop predates the C3 convention the review itself ordered; the review records
  it as the obsolete-convention artifact and its zero-based V2 adaptation passes.
* `test_boundary_inventory`: **26 failures, name-set byte-identical** to Child A's accepted
  baseline; `tokens.py` **0 unowned**.
* `test_token_lifecycle`, `test_expiry_reclaim`, `test_governed_endings`,
  `test_connected_lifecycle`, `test_reclaim_selector`, `test_intake`, `test_single_worker`:
  **all PASS**. `test_dependencies` 73, unchanged and pre-existing. Bounded to the suites this
  authority actually touches, as the review directed -- no seventeen-suite sweep.

### The catalog moved with the code, twice, and the probes caught both

`renew`'s `seconds` delegation has now been re-pointed three times in total, each time by
measurement rather than by reading: a self-delegation while the deadline was composed inside
the callback; removed when hoisting made the entry layer-owned and `test_no_entry_is_owned_twice`
caught the duplicate; and now pointed at `_extended`, where the composition actually lives.
And `renew`'s `token.owner` declaration became STALE when the body moved -- `renew` no longer
reads that member -- so it is withdrawn with the reason recorded beside it, not deleted
silently. `test_no_declared_owner_is_stale` is what found it.

### Remaining

1. C5, the reviewer's final bounded candidate/path/digest/evidence review.
2. Unchanged and still stated: no production consumer calls `renew`; the brief excludes
   consumer migration.

## 2026-09-27 claim 281597 — C1 closed: expired, ambiguous, or nothing

Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     acc419fe89db   PRODUCT
    work/.../test_renewal_arbitration.py                  d21f290efd15   selector, 44 cases

Reproduced `review_expiry_clock_gap_20260927.py` first: **1 FAIL**. The window was between
OBSERVING expiry and RECORDING it -- the clock moved backwards in between, my conditional
write declined, the caller stayed refused, and the next attempt renewed. Same token, same
revision, no competing renewal.

### The correction: the observation travels, and there are three outcomes

`_owning`'s expiry refusal now CARRIES the reading it was made on -- deadline, revision and
instant -- as a typed attribute on the refusal. That removes the last of the message matching
too: only an expiry refusal carries an observation, so the operand selects the path and the
prose is irrelevant.

`_judge_expired(control, domain, generation, observed)` compares that reading with what
stands, under its own write lock, and answers one of exactly three things:

* **expired** -- still past the CURRENT deadline: the authoritative record commits, as before;
* **ambiguous** -- the clock has moved BACKWARDS since the observation, at the same revision:
  neither "expired" nor "live" is true, so `resource-token.timing-ambiguous` records BOTH
  readings and further renewal is refused until somebody reconciles. TOK-9: "Ambiguous timing
  means hold/reconcile";
* **nothing** -- the revision has moved on, so a renewal overtook the observation. That is the
  previous claim's race and it stays closed: no record, and the renewed generation is none of
  the stale caller's business.

Each outcome is its own short transaction that decides its own condition; the second is
attempted only after the first has rolled back, so nothing is nested and no lock is held
across anything external.

`_owning` refuses while a hold stands (settlement paths pass `reclaiming=True` and are
unaffected), and `token_of` reports `timing_ambiguous` with both readings -- a reader that hid
the hold would let a caller believe a live token is simply live.

### Six new cases

The exact window and the retry that must fail; the record carrying both readings and claiming
NO expiry; the hold is not a release -- the resource stays outstanding, a competitor stays
excluded, and once the deadline genuinely passes the ordinary revocation still reclaims it, so
a hold is not a way to lose a resource; a fresh handle reads the same hold; an OVERTAKEN
observation is NOT an ambiguity; and a genuine expiry is still judged expired and not swept
into the new outcome.

### Measured

* `test_renewal_arbitration.py`: **44 PASS 0.142s** (38 preserved, 6 added).
* `review_expiry_clock_gap_20260927.py`: **OK**. `review_stale_expiry_judgement_20260927.py`:
  **OK** -- the earlier correction is preserved, which is what the "overtaken" outcome exists
  to keep true.
* `test_boundary_inventory`: **26 failures, name-set byte-identical** to Child A's accepted
  baseline; `tokens.py` **0 unowned** (the new records are private identities, so no new
  receiving entries).
* `test_token_lifecycle`, `test_expiry_reclaim`, `test_governed_endings`,
  `test_connected_lifecycle`, `test_reclaim_selector`, `test_intake`, `test_single_worker`:
  **all PASS**. Bounded to what this authority touches, as directed.

### What a reconciliation of an ambiguity hold would need, stated rather than implied

Nothing in this build clears a timing-ambiguity hold. That is deliberate for this bounded
Work -- the hold is the honest state and inventing a self-clearing rule would be the kind of
"asking again resolves it" the requirement forbids -- but it means an operator reconciliation
path is owed. The resource itself is never lost: revocation still reclaims it once the
deadline genuinely passes, which is proved above.

### Remaining

1. C5, the reviewer's final bounded candidate/path/digest/evidence review.
2. A supported reconciliation for an ambiguity hold, if the owner wants one; recorded here as
   owed rather than silently absent.
3. Unchanged: no production consumer calls `renew`; the brief excludes consumer migration.

## 2026-09-27 claim 281669 — one exhaustive decision on one snapshot, and a duplication I caused

Files changed, with digests:

    v12/python/src/baton_v12/worker_manager/tokens.py     73079b182348   PRODUCT
    work/.../test_renewal_arbitration.py                  ee23c4c7ca01   selector, 46 cases

Both findings reproduced first: `review_judgement_atomicity_20260927.py` **2 FAIL**.

### P1a — two conditional writes are not an exhaustive decision

My previous cut made two decisions in two transactions, each on its own snapshot, so a clock
that changed between them made BOTH decline: no expiry record, no ambiguity record, and the
retry renewed. There is now ONE transaction. It takes the write lock, reads the acquisition,
the committed renewals, the deadline they imply and the instant ONCE, and classifies
exhaustively:

* the observation does not correlate with what stands -> **nothing** is recorded (it was
  overtaken by a renewal, which is the earlier correction, kept);
* it correlates and the deadline has passed -> **expired**;
* it correlates and the deadline has not passed -> **ambiguous**, as the ELSE branch, so a
  correlated observation can never leave both records absent.

One short write under its own lock, using the same `BEGIN IMMEDIATE`/`_record`/`COMMIT` shape
`acquire` uses, nothing nested, no external I/O. A record already committed under either
identity is answered rather than written, so a second judgement replays the first.

### P1b — the observation is now one read

`_owning` derived the deadline from `_deadline_of` and then read the renewal count AGAIN, so a
renewal committing between the two produced an OLD deadline beside a NEW revision -- and the
correlation check, comparing only the revision, accepted it and held a token whose real
deadline had never passed. The pair now comes from ONE list of committed renewals, and the
judgement correlates BOTH members.

### A duplication I caused, and how it was caught

My first attempt at the single-transaction rewrite sliced the file between
`def _judge_expired` and `def _observed_revision` -- and `_observed_revision` is defined
BEFORE `_judge_expired`, so the slice DUPLICATED a 184-line region instead of replacing it.
Python took the later definition, which was the superseded two-transaction version, so the
probe kept failing while the new code sat unreachable above it. I found it by instrumenting
the transactions actually taken (`TRANSACT KINDS SEEN: ['resource-token.expired',
'resource-token.timing-ambiguous']`) rather than by re-reading my patch, then removed the
duplicated block after asserting on both copies' content. The file now holds exactly one of
each helper. This is the same duplicate-definition hazard Child A's review caught in
`test_stage_execution.py`; this time I caused it and it cost a measurement to find.

### The reviewer's P1b probe can no longer reach its seam, and the property is proved directly

`review_judgement_atomicity_20260927.py::test_torn_observation_cannot_hold_a_successful_renewal`
tore the observation by patching `tokens._deadline_of` and renewing between `_owning`'s two
reads. The correction the review ordered REMOVED that seam -- `_owning` no longer calls
`_deadline_of` at all -- so the probe's schedule never fires, its renewal never happens, and
the renewal under test simply succeeds. It now fails structurally rather than by finding a
defect, at `def paused(control, domain, generation, acquired=None)`.

So the property is proved at the decision instead, where it cannot depend on a seam: a torn
pair -- revision 1 beside revision 0's deadline -- handed straight to `_judge_expired`
correlates with nothing that stands, so nothing is recorded and the renewed generation keeps
its deadline. Its companion case proves exhaustiveness the same way: a CORRELATED observation
always leaves exactly one record, expired with the clock left alone and ambiguous with the
clock moved back.

### Measured

* `test_renewal_arbitration.py`: **46 PASS 0.150s** (44 preserved, 2 added).
* `review_judgement_atomicity_20260927.py`: case 1 (`two_decisions_cannot_leave_expiry_unrecorded`)
  **ok**; case 2 fails structurally as above.
* `review_expiry_clock_gap_20260927.py` **OK**, `review_stale_expiry_judgement_20260927.py`
  **OK** -- both earlier corrections preserved.
* `test_boundary_inventory`: **26 failures, name-set byte-identical** to Child A's accepted
  baseline; `tokens.py` **0 unowned**.
* `test_token_lifecycle`, `test_expiry_reclaim`, `test_governed_endings`,
  `test_connected_lifecycle`, `test_reclaim_selector`, `test_intake`, `test_single_worker`:
  **all PASS**.

### Remaining

1. C5, the reviewer's final bounded candidate/path/digest/evidence review.
2. An operator reconciliation for an ambiguity hold: still owed, still recorded as owed.
3. Unchanged: no production consumer calls `renew`.
