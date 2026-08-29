# Own runtime lane capacity across predecessor and successor attempts

## Discovery and parent

Discovered during W32382 correction re-review under
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.

## Confirmed gap

The manager has no lane/capacity identity spanning runtime attempts.
`posture_slots` is keyed by `(runtime_attempt_id, posture)`; a successor gets a
different slot and no runtime-start precondition consults a predecessor whose
container is absent but whose credential/launch teardown or cleanup remains
unsettled. The current test can start a successor only after cleanup, but the
same successor would also start before cleanup, so order in the test is not an
enforced invariant.

Authority claim capacity and manager runtime cleanup answer different times:
an assignment may end and release its authority claim while its process domain
or mounted roots still require cleanup. A new claim/attempt must not turn that
gap into overlapping execution. The lane key must also remain compatible with
W16821/W16823's canonical-principal and effective-scope correction rather than
hardening endpoint spelling as capacity identity.

## Required boundary

- Pin one authority/manager-owned lane identity that is not `attempt_id` and
  remains stable across predecessor/successor attempts and restart. State how
  it relates to Work, canonical principal, scope and assignment generation.
- Occupy the lane before the first writable runtime start, atomically with the
  manager fact that makes the start eligible.
- Keep it occupied while any predecessor runtime identity, uncertain
  observation, custody obligation, credential/launch root or retryable cleanup
  remains unsettled.
- Release it only on positive runtime absence plus every applicable provider
  ending and custody/cleanup decision. Crash/retry must neither leak nor
  double-release capacity.
- Refuse a successor before reaching the engine; after release, one racing
  successor wins and all others fail closed.

## Acceptance

- With one predecessor cleanup held open by an unresolved launch root, a real
  successor offer/claim/activation reaches no engine and no delivery.
- After exact absence and provider settlement release the lane, one successor
  starts exactly once; concurrent successors, restart and exact retry preserve
  one winner.
- Uncertain observation, provider retry, retained/quarantined material,
  cancellation and failed cleanup have explicitly ruled lane effects.
- Two endpoint addresses mapped to one principal cannot gain two lanes; two
  distinct principals/scopes are isolated according to the W16821/W16823
  authority decision rather than participant-prefix parsing.
- Projection explains the current lane holder and blocking predecessor without
  exposing a mutable caller-selected principal or scope.

## 2026-08-29 — the lane, pinned and implemented

**The gate cleared legitimately.** W16821 and W16823 are both closed
satisfying, so the canonical principal and effective scope exist and W16823
carries them onto the activated attempt row. Revalidated before acting rather
than transcribed: manager schema 12, `assignment_principal` and
`assignment_scope` present on `attempts`, and no `runtime_lanes` table.

### The identity, pinned

    lane = (authority_uuid, work_id, principal, effective_scope)

- **not the attempt id**, which is the whole point: an identity that changed
  with every attempt could not span a predecessor and a successor;
- **not the generation**, because a successor claims after a fence and mints a
  new one, so a generation-keyed lane would be free for exactly the caller it
  must block. Generation stays the §4 execution FENCE; fencing and capacity are
  different questions asked at different moments;
- **not the participant**, because W16821's finding is that two spellings of
  one person received two of everything. The acceptance names that outcome as a
  failure and the PRINCIPAL is what W16823 now supplies;
- **the scope is in it** because two decisions in two authorization domains are
  two authorizations, and this manager consumes the authority's answer rather
  than deriving one;
- **the Work is in it** because a lane protects an assignment's MATERIAL, and
  two Works held by one principal are two sets of roots with nothing between
  them.

Occupied by an `INSERT` on that key -- the primary key IS the compare-and-swap,
so there is no read-then-write window -- inside the same transaction that
journals the start. Released by a `DELETE` bound to the holder, inside the
transaction that ends the cleanup axis.

### The hole the key alone leaves, named rather than left

The authority's claim slot is per PRINCIPAL, so a Work whose assignment ended
may be reclaimed by a DIFFERENT principal while this manager's cleanup is open.
That successor's lane is a different row -- which is what "two distinct
principals are isolated" requires -- so the key alone would let it start.

`_no_predecessor_holds` is therefore a SECOND precondition rather than a third
key part: a start also requires that no lane over the same
`(authority_uuid, work_id)` is held by anyone. Keeping them separate keeps the
two facts separate -- capacity is per principal, the predecessor interlock is
per Work -- and each is proved on its own.

### The ruled lane effects, measured

| ending | lane |
|---|---|
| cleanup `complete` | released |
| cleanup `retained` | released -- retained material lives in CUSTODY, a manager-owned sibling the worker never sees, so a successor collides with nothing |
| cleanup `failed` | HELD -- the destroy was ordered and the runtime survived it; a lane released while a container is still there is the overlap this exists to prevent |
| provider unresolved | HELD -- not an ending at all; the axis never moved |
| uncertain observation | HELD |
| cancellation | HELD until cleanup ends |

### What is proved and what is not

Every guard is measured BY REMOVAL --
`evidence/w32649-mutations-2026-08-29.txt`, eight mutations and eight named
failures. The successor case proves the adapter was asked NOTHING, which is the
engine witness the acceptance asks for, against the injected adapter this
manager's own suites use; the concurrent-winner case races three real threads
over one store file.

**Not proved here:** the acceptance's "a real successor offer/claim/activation"
over a real daemon. The offer path allows one live offer per Work, and the
window this lane is about is precisely the one where the authority would let a
second claim through -- so a successor is built by writing the columns
`activate_assignment` writes rather than by driving an offer. That is named as
a limit of the case rather than represented as the full arc.

## 2026-08-29 — independent review correction

**Confirmed:** the real successor arc is possible in the existing fixture and
the statement above is superseded. `offers_one_live_per_work` holds only
`issued` and `accepted`; the predecessor's offer is already `claimed`, so it
does not prevent a second offer. The additive
`test_a_real_successor_claim_reaches_no_engine_or_delivery` now drives
`issue_offer` → `accept_offer` → `record_attempt` → `submit_claim` →
`activate_assignment` and proves the open predecessor lane refuses the start
before input-root authorization and before the engine. The case passes.

**Confirmed review finding:** the persisted lane is a five-member relation --
the four stored authority-owned identity parts and the `lane_id` derived from
them -- but both projection read paths validate only the independent column
types. If an adopted row's `lane_id` no longer derives from its stored parts,
`runtime_lane` can report no holder, no ownership and no blocker while that row
still holds capacity. This violates the acceptance's explanatory projection
and the manager's receiving-trust-domain rule. The additive
`test_a_persisted_lane_must_derive_from_its_stored_identity` demonstrates the
gap and currently fails. The correction must own the relation on every adopted
lane row before using it; it must not guess which half of a split identity is
authoritative.

**Confirmed additional coverage:** two successors under distinct principals
have distinct lane primary keys, so their race is decided by the per-Work
interlock inside the write transaction rather than by the lane primary key.
`test_concurrent_principals_still_produce_one_work_holder` exercises that exact
race and passes with one holder.

## 2026-08-29 — the [P1], and a claim of mine the review disproved

**Confirmed [P1]: the split identity was projected as free.** `lane_id` is
DERIVED from the four identity parts stored beside it, so the five values are
one relation rather than five independent well-typed strings.
`boundaries.row` proved each and said nothing about whether they still belong
together — and the consequence is exactly the one a capacity record must never
produce: an adopted row keeping its holder and its parts but carrying another
well-formed `lane_id` was missed by `_holder_of` (which looks up by the
recomputed key) and then dropped from `blocked_by` by `runtime_lane` (which
excludes rows the queried attempt holds). The projection answered
`holder=None`, `held_by_this_attempt=False`, `blocked_by=[]` while the capacity
row was still there. An operator was told the lane is FREE.

**Corrected at the adoption, once, for both read paths.** `_adopted` recomputes
the name from the stored parts and refuses `integrity/schema` when they
disagree. Neither side of the split is chosen: a row where the name and the
parts disagree does not say which half moved, and picking one would invent the
answer the refusal exists to withhold. Both read paths come through it, and a
second case drives the by-Work path specifically — a row belonging to another
principal is never looked up by the recomputed name at all, so a guard on the
first path alone would have left the second answering out of a broken row.

**Confirmed — my acceptance limitation was wrong.** I reported that a real
successor offer/claim/activation could not be driven because the live-offer
index allows one per Work. The reviewer measured it: that index covers only
`issued` and `accepted`, and a CLAIMED predecessor has already released the
slot. The successor case they added and passed drives the public
`issue_offer`/`accept_offer`/`record_attempt`/`submit_claim`/
`activate_assignment` arc and proves the held predecessor lane wins before
input-root authorization and before the adapter — which is the acceptance
sentence I had recorded as unreachable.

**Confirmed — the per-Work interlock is decisive inside the transaction.** The
reviewer's second addition races two successors with DIFFERENT principals, so
their lane ids differ and the primary key cannot be what decides it. One
winner: the interlock runs inside the serialized write, not beside it.

## 2026-08-29 — correction re-review: two persisted reads remain outside adoption

**Confirmed [P2]: the correction owns the public projection reads, not every
persisted lane read.** `_no_predecessor_holds` selects only `lane_id`, `holder`
and `reason`, then reports an adopted split relation as ordinary predecessor
contention. `_occupy_lane` does the same with `holder` and `reason` after an
insert conflict. Neither path calls `_adopted`, so neither proves that the
stored lane id still derives from its four stored identity parts before using
the row.

This remains fail closed against concurrent execution, so it is lower severity
than the original free-lane projection. It is still not a harmless diagnostic
difference: the manager can classify corrupt capacity as a normal race loser or
predecessor, leave the Work permanently blocked, and direct recovery toward a
holder whose persisted relation it never accepted. Receiving-trust-domain
ownership applies before any use of persisted state, not only before public
projection.

Two additive regressions pin both paths. A split row found by the predecessor
query and a split row reached only after the lane primary-key conflict both
currently return `refused/precondition`; each must instead return the manager's
`integrity/schema` refusal before using its holder or reason. The common repair
is to adopt the complete row on all four read paths, then extend the boundary
inventory so it enumerates these two reads as well as `_holder_of` and
`_work_lanes`.

## 2026-08-29 — every persisted lane read owns the relation

The previous correction wired the two PROJECTION reads through `_adopted` and
left the two START reads selecting partial rows. That cut was wrong:
`_holder_of` and `_work_lanes` read this relation to answer about it;
`_no_predecessor_holds` and `_occupy_lane` read it to decide whether a runtime
may exist.

Both now adopt the complete row. A split relation is `integrity/schema` at
either, rather than an ordinary predecessor at the first or an ordinary race
loss at the second — and the second is the path a moved Work part takes,
because it evades the predecessor query and is met at the retained primary key.

The boundary inventory enumerates all four reads, which is what stops the
omission recurring.

## 2026-08-29 — independent final review

**Confirmed corrected:** `_no_predecessor_holds` and `_occupy_lane`'s
primary-key-conflict path now select complete `runtime_lanes` rows and pass
them through `_adopted` before using holder or reason. A split derived identity
therefore refuses as `integrity/schema` instead of being reported as ordinary
predecessor contention or an ordinary race loss.

**Confirmed recurrence guard:** the receiving-boundary inventory names all
four persisted lane reads. Its probe-arrival gate passes independently, and
reverting either start-path adoption makes the exact additive regression fail.

**Accepted terminally:** the previously accepted lane identity, public
successor arc, in-transaction per-Work interlock, concurrent winner, provider
and cleanup effects, restart behavior and projection remain intact. W32649
satisfies its acceptance and may close.
