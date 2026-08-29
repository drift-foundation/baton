# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — the sequencing gate installed; nothing implemented

Claimed W32649 at seq 32909. **No production code was edited.** No Git history
or index was mutated.

### The gate was named in the thread and was not on the ledger

Message 32655: *"this lane identity must consume W16821/W16823 canonical-
principal manager context rather than harden endpoint spelling. The impl Route
must install the appropriate W16823 dependency **before production edits**;
readiness without that edge is not authorization to guess the capacity
identity."*

Checked rather than assumed: W32649 had **zero blockers**, so readiness
offered it anyway. That is the fourth time in this campaign a stated order was
absent from the ledger (W16821, W32391, W32382, and now this), and the remedy
is the same each time. I hold the impl Route, so installing it is my act:

    block work=W32649 on=W16823   seq 32915

The chain is real rather than nominal — **W32649 → W16823 → W16821** — and
W16821 is itself parked pending the approver ruling on the schema-1
disposition, which I recorded when I held it.

### The dependency is load-bearing, not procedural

This is worth separating from the ordering point, because it is the reason
guessing would be wrong rather than merely early. The bound acceptance says:

> Two endpoint addresses mapped to one principal cannot gain two lanes; two
> distinct principals/scopes are isolated according to the W16821/W16823
> authority decision rather than participant-prefix parsing.

The lane KEY is therefore the canonical principal and effective scope — which
do not exist yet. W16821's own finding is explicit that today one
`team.member` string serves as endpoint, principal, capability grantee,
claim-slot key and audit actor, and that two spellings of one person receive
two claim slots. A lane keyed on anything available today would reproduce
exactly the defect W16821 exists to remove, and the acceptance names that
outcome as a failure.

### What I did NOT do

No lane identity pinned, no occupy/release seam, no tests. PLAN's first
substantive item is the identity, and every later one is derived from it.
Choosing a key now would be deciding W16821's ruling by implementing against
it — the same error I avoided on W32577 and the one W32382's review caught in
my own test.

## State

**Blocked on W16823 (and through it W16821), unclaimed.** Implementation-ready
when the canonical principal exists. The confirmed boundary and acceptance are
the reviewer's and are untouched.

## 2026-08-29 — the gate cleared, and the lane is implemented

Claimed W32649 at seq 35769. **No Git history or index was mutated.**

### The block I installed cleared the way it was supposed to

W16823 is closed satisfying and W16821 through it, so the edge I installed at
seq 32915 did its job: this wake is the intended order arriving as an edge
rather than as a coincidence. And the dependency was load-bearing rather than
procedural, which is now visible in the code: `lane_reference` reads
`assignment_principal` and `assignment_scope`, two columns that did not exist
when this Work was first offered to me.

### The identity, and the three things it deliberately is not

`(authority_uuid, work_id, principal, effective_scope)`.

Each exclusion is its own argument rather than one. **Not the attempt id**, or
it could not span the two attempts it exists to relate. **Not the generation**,
because a successor mints a new one after a fence -- so a generation-keyed lane
would be free for exactly the caller it must block, and §4's fence and this
capacity are different questions at different moments. **Not the participant**,
because W16821's whole finding is that two spellings of one person received two
of everything, and the bound acceptance names a two-lane outcome as a failure.

### The hole the key alone leaves, which I did not leave unnamed

The authority's claim slot is per principal, so a Work whose assignment ended
can be reclaimed by a DIFFERENT principal while cleanup is open -- and that
successor's lane is a different row, which is what the acceptance's "two
distinct principals are isolated" requires. The key alone would let it start.

So the predecessor interlock is a SECOND precondition asked of the whole
`(authority_uuid, work_id)` rather than a third key part. Capacity is per
principal; the interlock is per Work; each is proved by its own case. If a
reviewer wants those combined into one key instead, they are separable -- but
I would rather be told that than quietly widen an identity the acceptance
spells out.

### Where the two acts sit, and why there

**Acquire** is inside `request_runtime_start`'s journalled transaction, because
that transaction IS "the manager fact that makes the start eligible" -- it is
what a restart reads to decide a start was requested. A lane taken anywhere
else leaves a window where the journal says a start is under way and the lane
says nobody is executing.

**And asked once BEFORE it**, as an early read, because authorizing an input
root is itself a durable act and a successor that cannot start must not perform
one. That read is not the decision and is not the only check: the `INSERT`
inside the transaction is what decides the race, with the lane's primary key as
the compare-and-swap and no window at all. A case proves the ordering by
showing a blocked successor is refused with the LANE's message rather than the
input-root boundary's.

**Release** is inside the transaction that ends the cleanup axis, which is the
only place where positive runtime absence, every applicable provider ending and
the custody and retention decisions are all true at once.

### The ruled effects, each measured

`complete` and `retained` release; `failed`, an unresolved provider, an
uncertain observation and a cancellation all HOLD. `retained` releasing is the
one worth arguing: retained material lives in custody, a manager-owned sibling
the worker never sees, so a successor collides with nothing -- and holding for
it would stop the Work forever on a policy decision.

### What I am reporting rather than claiming

The acceptance asks for "a real successor offer/claim/activation" over a real
daemon. The offer path allows one live offer per Work, and the window this lane
is about is precisely the one where the authority would let a second claim
through -- so the successor in these cases is built by writing the columns
`activate_assignment` writes, not by driving an offer. The lane, the interlock
and the release are exercised through the production functions; what is
simulated is the second claim's arrival. I would rather name that than let a
fixture stand in for the arc.

### Gates

- `tests/manager/test_runtime_lane.py` -- **22 tests, OK**;
- the four real-daemon serial suites -- **97 tests, OK**, 4 Podman skips;
- full v12 parallel source -- **8 failures, 1 error on 1820 tests**, which is
  byte-for-byte the shard set and count this round started at: two
  `test_work_labels` shards (W29400's) and six `test_boundary_inventory` shards
  whose contents are the pre-existing families. Every boundary this cut opened
  is probed -- the eight `runtime_lanes` column entries were unprobed when I
  first measured and are covered now by a derivation over the table contract,
  so the inventory's missing and stale lists carry no lane entry at all.
  Transcript: `evidence/w32649-gate-2026-08-29.txt`.
- every guard measured BY REMOVAL --
  `evidence/w32649-mutations-2026-08-29.txt`: eight mutations, eight named
  failures. One started as a SKIP -- the early pre-durable check, which I first
  called a deliberate equivalence. It was not one: I had no case that could
  tell the two orderings apart, so I wrote it rather than leave an unmeasured
  claim in a harness whose whole point is that there are none.

## State

**PLAN 1-5 done. Passed back for independent review.**

## 2026-08-29 — the [P1] corrected, and a claim of mine disproved

Reclaimed W32649 at seq 36088. **No Git history or index was mutated.**

### The finding

`lane_id` is derived from the four parts stored beside it. I owned each column
and not the relation between them — so an adopted row whose name no longer
derives from its own parts made the public projection answer that the lane was
FREE while the capacity row sat there. That is the one answer a capacity record
must never give, and it is worse than any refusal.

`_adopted` now recomputes the name from the stored parts at the point of
adoption and refuses `integrity/schema` when they disagree. It chooses NEITHER
side of the split: a row where the two disagree cannot say which half moved.
Both read paths come through it, and I added the by-Work case because a row
belonging to another principal is never looked up by the recomputed name — a
guard on `_holder_of` alone would have left `_work_lanes` answering
`blocked_by` out of a row whose identity does not hold together. Both
directions of the guard are measured by removal.

### Two things I got wrong that the review measured

**The successor offer.** I reported that a real successor
offer/claim/activation could not be driven, because the live-offer index allows
one per Work. It covers only `issued` and `accepted`, and a CLAIMED predecessor
has already released that slot — so the arc I recorded as unreachable was
reachable the whole time, and the reviewer wrote it and it passes. What I
should have done is what I did for the frozen `assignmentManifest` two rounds
ago: read the index definition rather than reason from what the offer path
usually does. I named the limit honestly and the limit was not real, which is
the same shape as W34884's "this suite has no seam for it".

**What actually decides the cross-principal race.** My concurrent case raced
three successors sharing one lane, so the primary key could have been the whole
story. The reviewer's races two with DIFFERENT principals: their lane ids
differ, so only the per-Work interlock inside the serialized transaction can
produce one winner. My case could not have distinguished those two mechanisms;
theirs does.

### Gates

- `tests/manager/test_runtime_lane.py` — **27 tests, OK**, including the
  reviewer's three additions and the two this round added;
- every guard measured BY REMOVAL —
  `evidence/w32649-mutations-2026-08-29.txt`: **ten** mutations, ten named
  failures, both directions of the new relation guard among them;
- the full gate and the serial lifecycle suites: see
  `evidence/w32649-gate-2026-08-29.txt`.

## State

**Passed back for independent review.**

## 2026-08-29 — the other two lane reads

Reclaimed W32649 at seq 37548.

### [P2] Two reads of the same relation never adopted it

The finding is right and the shape of my previous correction is what caused
it. I centralized the stored-id/parts invariant in `_adopted` and wired the two
PROJECTION reads through it — and left the two START reads alone, selecting
three columns and two columns respectively and using them directly.

The distinction I had in my head was "public reads", and it was the wrong cut.
`_holder_of` and `_work_lanes` read this relation to ANSWER about it;
`_no_predecessor_holds` and `_occupy_lane` read it to DECIDE whether a runtime
may exist. The second pair is the more consequential one.

What each cost:

- **`_no_predecessor_holds`** reported a split row as an ordinary predecessor —
  `refused/precondition`, carrying a holder and a reason out of a relation this
  manager never owned as one. Corrupt persisted authority hidden behind normal
  contention, and recovery pointed at an attempt id the row may not be about.
- **`_occupy_lane`'s conflict path** is the subtler one: a row whose stored
  Work part has moved is no longer SELECTED by the predecessor query, so it
  evades that check entirely and is met at the retained primary key instead —
  where two columns were read straight out of it and reported as an ordinary
  race loss.

Both now select the complete row and pass it through `_adopted` before any
member is read.

**The review's severity call is right and worth keeping.** Both outcomes still
prevented overlap, which is why this is [P2] and not a repeat of the [P1].
But "the outcome happened to be safe" and "the state was understood" are
different statements, and a Work left permanently blocked by a row nobody can
diagnose is the cost of confusing them.

### The inventory now enumerates all four

`lane_probes` covered `_holder_of` and `_work_lanes`. It covers
`_no_predecessor_holds` and `_occupy_lane` too, each with its own driver:

- a PREDECESSOR's row, held by another attempt over the same Work, spoiled,
  read by a successor's start;
- a COLLIDING row held by this attempt — so the predecessor query excludes it,
  which is exactly the path the review found — carrying the derived `lane_id`
  so the insert really conflicts.

An inventory that enumerated only the projection pair is how the start pair
came to use partial rows in the first place, so this is the part of the
correction that stops it recurring.

### Gates

- `test_runtime_lane` — **29 tests, OK**, both reviewer regressions among them;
- two mutations, two named cases (`evidence/w32649-mutations-round3-2026-08-29.txt`);
- `test_attempts` 228, `test_intake` 74, `test_dependencies` 21,
  `test_secrets` 90, `test_text_sweep` 3 — OK;
- the boundary inventory's probe-arrival check, and the complete serial
  registry.

## State

**The [P2] is corrected.** Passed back for independent review.
