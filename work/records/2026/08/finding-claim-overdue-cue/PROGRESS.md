# Progress

Implementer-owned. Work `W2938`, reclaimed by `baton.claude` 2026-08-20 after
the ownership supersession and the pinned participant-level contract.

## The superseded implementation is gone (PLAN item 3)

Removed: `claim_cell`, the Jobs `CLAIM` column and its drop-order entry, the
`CLAIM` row cell, the Work-detail claim suffix, the whole
`test_w2938_claim_overdue_cue.py` suite, its `Claim`-vs-`pickup` parity check,
and the documentation paragraph describing the per-Job cue.

Preserved, because it was separately approved: the Jobs `New` column stays
removed, with no replacement. Personal unseen state is untouched everywhere it
drives an action.

## The participant contract (PLAN item 5)

### One-slot capacity — the thing everything else needs

`transitions.claim_work` refuses a second live claim, naming the Work already
held and the three ways out. This is not presentation: without a defined
capacity unit, "at least one eligible member has free capacity" is
unanswerable and the whole cue would be dishonest.

### The opportunity interval is canonical

New schema 25 table `member_pickup(team, member, started_seq, started_at)`.
One row exists exactly while a participant is idle with a nonempty actionable
pool — so the interval survives a client or runner restart, which a client-side
timer could not.

It is maintained by `_sweep_pickup`, called from `Authority._write` — the ONE
mutation boundary. That placement is deliberate: a dozen transitions can change
somebody's pool or busy state, and a sweep that each of them had to remember
is a sweep that gets forgotten. It runs in the same transaction as the change
that moved it, so no reader ever decides canonical state.

The pool is computed from the same predicate the participant-relative `wait`
uses — open, ready, neither blocked nor parked, and the member is a live
handler of that Work's own route — recomputed in the write transaction rather
than imported from the projection.

### Threshold

`instance.pickup_overdue_seconds` is optional deployment policy, validated
positive at acceptance and stored in `meta`; `PICKUP_OVERDUE_DEFAULT` is 360.
The accepted value rides the `teams` read as `pickup_overdue_seconds`, so no
client carries a private threshold or recomputes against a local guess.

One thing this exposed: `member_pickup.started_at` initially used the
millisecond clock while readers compare against `store.clock()`, which is
second-precision — so the first second of every interval read as zero and a
1-second threshold was unreliable. Both now use the same second-precision
instant, added as `authority.utc_now()` beside the millisecond helper.

### Presentation

- Teams member rows carry `Pickup` — `-`, `pend`, `late` — placed beside
  `Work` (what this member is executing, and whether they owe a pickup they
  have not made) and last in the drop order but for `State` and the identity.
- An overdue member's row is bold, composing with the selection highlight
  rather than replacing it.
- Member detail gains a `Claim pickup` section: the full word, the elapsed
  interval, the start, and the canonical first actionable Work as a suggested
  next claim. Absent entirely when nothing is owed.
- `[Teams *]` when at least one participant is overdue, reusing the Inbox `*`
  vocabulary. Pending alone never stars, and the star carries no count. It is
  read from the same cached roster the Teams tab is drawn from, so the star and
  the rows it sends the operator to cannot disagree.
- Jobs and Work detail carry nothing.

## Adapting the suites

One-slot capacity broke 10 tests across 7 files — far fewer than the 23 files
that claim repeatedly, because most claims are sequential. Every one of them
wanted several rows CLAIMED AT ONCE:

- `test_w12` and `test_w78` build a row per scheduler state; the rows that
  merely pass THROUGH a claim are now built before the one that stays claimed.
  Ordering, not a second claimant — those fixtures resolve to one member, and
  inventing a handler to preserve the old order would be changing the world to
  suit the sequence.
- `test_w33` and `test_w47` prove a batched read across MANY claimed rows, so
  they now use many claimants through a new `fixtures.build_crew` helper. That
  property would have quietly weakened to one row otherwise.
- `test_revisions` needed no claim on the second Work at all; `test_w23`'s
  second bold form is now the other one the rule names (ready, unclaimed,
  routed to the viewer), which keeps both forms of BOLD present.

The `New` removal also freed enough width at 70 columns for `Next` to survive,
and the Title absorbed the difference — so `test_w154`'s cue-ordering assertion
now checks the ordering STRUCTURALLY (whatever fits after the cue is a prefix
of the title) instead of against a fixed number of title characters.

## Regressions (PLAN item 6)

`tests/work/test_w2938_participant_pickup.py`, 39 cases:

- one-slot capacity: the refusal, what it names, that every releasing
  transition frees the slot, and that a second participant is unaffected;
- one obligation: ten Jobs make ONE interval, not ten; adding, reprioritizing
  and a competing claim do not reset it while the pool stays nonempty; a busy
  participant owes nothing while a teammate still does; claiming ANY eligible
  Job clears it; becoming idle again starts a NEW interval whose elapsed time
  is zero; an emptied pool clears it;
- what is not a pool: blocked, parked, terminal, and lost route eligibility
  through a real `regen`;
- the shared route: every idle eligible member evaluates its own interval, and
  after one wins, the loser's obligation is gone — the cue never bypasses the
  atomic claim;
- threshold: the default, pending-vs-overdue either side, a configured
  1-second deployment proving `overdue` for real, a non-positive value refused
  at acceptance, a read that mutates nothing, and the interval surviving
  reopening the authority;
- JSON: the roster publishes the state, the start, the elapsed seconds, the
  suggested Work and the accepted policy value; the suggestion follows the
  pool and does not own the obligation;
- console: the Teams `Pickup` column, the bold overdue row with `[Teams *]`,
  pending never starring, member detail spelling it out and staying absent when
  nothing is owed, the drop-order property, drop-whole-never-squeezed, and
  — the ownership supersession asserted where it was broken — no Jobs column,
  no Jobs cell and no Work-detail field;
- the PACKAGED artifact on a real terminal: `[Teams *]` on the Jobs screen, a
  `late` member row on Teams, and no pickup vocabulary in the Jobs table.

Confirmed non-vacuous for both halves separately: reverting one-slot capacity
fails 2, and reverting the `[Teams *]` star fails 2 more.

## Verification

- `test_w2938_participant_pickup.py` — 39 passed.
- Full v11 gate on the final tree — 2737 parallel, 52 serial, 55 ACP,
  all passed.

## 2026-08-20 — review round 1: changes requested

`review-2026-08-20T14-52-56Z.md`. All three confirmed; the reviewer's
deliberately-red regression is now green.

**P1 — `teams` could publish two snapshots.** Correct, and mine. `teams()`
read `pickup_threshold` before entering `_read_snapshot`, derived every
member state with that value, exited, and read it AGAIN for the response — so
a concurrent acceptance could publish states derived with threshold A beside a
response announcing threshold B. That contradicts both this feature's
one-accepted-value contract and the projection's own one-snapshot rule. The
threshold is now acquired once, inside the same snapshot as the roster, and
that exact value is returned.

**P2 — a malformed policy silently became a local guess.** Also correct.
`pickup_threshold` fell back to the compiled default when the accepted meta
value was missing, zero, negative or unparseable. But initialization and
acceptance ALWAYS store a validated positive value, including the default when
the document omits the field — so those cases mean the authority is invalid,
not that a deployment declined to choose. Falling back had the reader invent
policy in exactly the place the contract names as the only source of truth. It
now raises `WorkError`, and the defaulting stays at acceptance where omission
legitimately means 360.

**P2 — superseded prose in live tests.** The three cited comments explained
their width changes as "W2938 spent three more cells of the Title on the
`Claim` cue" — a design this record supersedes. Rewritten to name the actual
reason: `New` was removed with no replacement and the responsive layout
changed. I swept for the rest of the first attempt's residue; a fourth comment
in `test_w23_bold_title.py` referred to the capacity rule loosely and now names
it, and no other live prose mentions the retired column.

### Regressions added (now 48 cases with the reviewer's)

- the roster reads ONE policy per snapshot, counted rather than asserted
  indirectly;
- a missing accepted threshold fails closed, and so does `teams` through it;
- five invalid stored values fail closed — `0`, `-5`, empty, non-numeric and
  fractional;
- and the legitimate omission still accepts 360, so failing closed at read did
  not remove the default at acceptance.

Non-vacuous both ways: restoring the double read fails 2 (mine and the
reviewer's), and restoring the silent default fails 6.

Verification after the correction: the two W2938 suites 48 passed; full v11
gate 2746 parallel, 52 serial, 55 ACP.

## State

Awaiting independent review (round 2).
