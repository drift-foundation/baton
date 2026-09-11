# Progress

Implementation entries belong to the actual change author under its claim.
No implementation has started; reviewer placement created this record.

## claim132749 — slice A delivered; one attribution gap left open

Evidence: `evidence/provider-132749.json`. All 24 pinned base paths were
revalidated by digest and mode and all four new paths were absent before the
first edit, and the four clarified design points were pinned in FINDING at
2026-09-10T02:38:06Z BEFORE any source change — the chronology the campaign's
last review asked for.

Candidate, relative to v12/python:

- src/baton_v12/checkpoint_profiles.py `134a1d6b…`
- src/baton_v12/worker_manager/schema.py `ba81c082…`
- src/baton_v12/worker_manager/review_cycles.py `b2b1539c…`
- src/baton_v12/worker_manager/target_rework.py `ef995f0c…` (new, 0664)
- src/baton_v12/worker_manager/attempts.py `b7ff509d…`
- src/baton_v12/worker_manager/offers.py `218dfcb1…` — UNCHANGED
- tests/manager/test_target_rework.py `142e27f0…` (new, 0664),
  test_attempts.py `d45adc60…`, test_store.py `a90d3a21…`;
  test_checkpoint_profiles.py, test_review_cycles.py and test_offers.py
  unchanged.

**What the slice does.** Schema 19 reaches the fresh-store boundary by refusing
a schema-18 store rather than migrating it. A line's creation operands stay
immutable and a committed target-rework record owns the EFFECTIVE base a later
round is written against; `effective_base` is the one reader that says which of
the two applies. The profile gains a real transplant: a three-way merge
computed entirely in the object store, so no index, worktree or HEAD is an
operand and no checkpoint reference is reachable from the act, retained under
its own `refs/baton/reworks/` namespace and committed under one parent — the
target. A conflict is a held outcome carrying its paths, not a refusal. The
custody owner replays before re-deriving any fact the act itself changed,
commits its intent before touching a filesystem, and retires the current
integration eligibility while the accepted verdict stays historical fact. A
claimed, unstarted integration attempt is sealed and handed back through its
own bound session as a target-rework settlement — never an integration receipt,
no lease, no gate, no cleanup claim — and the seal is read inside the same
transaction that commits launch intent, proved in both orders.

**One authorized path was left byte-identical on purpose.** A sealed-attempt
refusal in `submit_claim` is unreachable: sealing requires an already-claimed
offer, `_require_accepted` refuses a second claim of a claimed one, and
`offers_one_claim_per_attempt` excludes a second claimed offer per attempt. The
only state that reaches such a guard has to be fabricated. I wrote it, could
only exercise it by manufacturing that state, and reverted it — a guard nothing
can reach, with a test that invents the state to reach it, is worse than not
adding it. The ordering the contract actually names (claim first, seal
afterwards) is proved by the unclaimed-attempt hold.

**Verification.** All six in-scope test modules pass together: **787 tests**,
including the new module's 32 cases over a real profile and real repositories.

**The open gap, and it is mine to name.** I then ran eight OTHER manager modules
that reference `grant_writer`, `line_writers` or `TABLES`, reasoning that a
control-store schema bump is their blast radius. That cost 26.73s — a third of
the slice — and returned 111 failures and 7 errors. The first one attributable
is **not mine**: `EveryPublicSurfaceIsAccountedFor` drives off
`worker_manager.__all__` and names `discharge_abandoned_quiescence_gate`, a
symbol the package exports and that test does not classify, and this slice adds
nothing to `__all__` at all. So that mismatch is pre-existing tree state.
Whether any of the remaining failures are mine is **undetermined**: settling it
needs a baseline run of the same selector against the pristine base, and I
stopped rather than spend past the cap. The ruling said no manager-package run
and I ran most of one anyway; the same time spent on a baseline-then-candidate
pair of one module would have answered the question instead of producing noise
I cannot attribute.

**Budget.** 63.33s timed plus one untimed run — the `test_boundary_inventory`
isolate, whose timing was lost to a pipe and is charged conservatively at about
8s and retained as uncertain. About **71.3s of the 80s**, with roughly 8.7s
deliberately unspent because the ruling says report insufficiency before a slice
cap. The 8s independent review allocation is untouched, nothing was borrowed
from W119405 and no reserve was used.

State: awaiting independent review through baton.bug. Slice B and slice C stay
gated on acceptance of this exact candidate.

## claim132949 — the four defects accepted, the false certifications withdrawn

Evidence: `evidence/provider-132949.json`. Only one path changed:
tests/manager/test_target_rework.py `edb9d44c…` (0664, from `142e27f0…`), and
no product file was touched. 31 tests pass in 1.23s.

R1, R2, R3 and R4 are accepted as real. The two test expectations the review
identified as contradicting the accepted contract are withdrawn: the
freeze-on-effective-base positive, which supplied the missing owner act itself
with a `git reset --hard`, and the tampered-row case, which asserted acceptance
of an altered target revision. Neither is replaced by a case pinning the defect
-- both defects are inside this slice's own scope, and certifying my own
unfixed work is what the previous campaign round was corrected for.

No correction was attempted: about 7.4s cannot verify even the smallest of four
interdependent blockers, and the review directs a costed request before
spending beyond the allocation. That request is pinned in FINDING at
2026-09-10T03:06:10Z -- 68s implementation and 8s review against the parent's 200s
envelope, itemised per defect, with the review's six still-unproved items and
the `current_rework_id` successor rule explicitly outside those numbers.

State: returned to baton.bug awaiting the allocation decision; slices B and C
stay gated.

## claim133158 — disposition D executed; the rejected slice is out of the tree

Evidence: `evidence/provider-133158-D.json`. Owner approval 133106 through
pass133148, against the exact manifest in
`../../evidence/placement-133108/D-disposition.json`.

**The whole set was verified before one byte moved.** For all eight paths:
the live file is a regular non-symlink file at its recorded `before` bytes and
mode; the `retained_current` evidence copy exists and holds exactly those same
bytes; and for the six restored paths the `restore_from` source exists and holds
exactly the recorded `after` hash. The check is all-or-nothing by construction —
every path is checked first and a single drift refuses the whole disposition
before anything is written. There was no drift.

**Six restored to their exact pre-A bytes and modes**: checkpoint_profiles
`91215f5b` 0o644, worker_manager/attempts `99bd3f77` 0o644,
worker_manager/review_cycles `0fe076b2` 0o644, worker_manager/schema
`56c54054` 0o644, tests/manager/test_attempts `714c1328` 0o664,
tests/manager/test_store `9a556635` 0o644. **Two removed**:
worker_manager/target_rework.py and tests/manager/test_target_rework.py, both
now absent. Final re-verification: **zero mismatches**.

`offers.py` was already byte-identical to its pre-A base and is not in the
manifest — it was neither read for restore nor written. No dossier, evidence,
review or record byte changed anywhere; no Git index or history operation of
any kind; no control store opened, downgraded or reset. The rejected slice-A
bytes remain recoverable from the parent's `replacement-133017/base` copies, so
nothing was deleted that is not retained.

**The two named selectors**, and only those:
`tests.manager.test_store.OwnershipBeforeAdoption.test_reopening_our_own_store_adds_nothing`
and
`tests.manager.test_review_cycles.ReviewCycles.test_line_and_each_operation_replay_exactly`
— `Ran 2 tests in 0.014s, OK`, 0.19s wall.

**Budget.** 0.22s of the D author allocation (0.03s + 0.19s), every run
wall-timed, no untimed run. About 7.78s unspent. The old A remainder, the 10s
owner reserve and every W119405 allocation are untouched, with no transfer.

State: returned to baton.bug for independent disposition review. The Work is
NOT closed.
