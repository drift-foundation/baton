# Progress

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — claimed; the ended-runtime restart slice

Claimed W32385 at seq 32482. No Git history or index was mutated.

### PLAN 1: revalidated

W6636's running-adoption, exact-observation and cleanup contracts hold on the
tree. This module subclasses that composition's fixture rather than restating
it, so these cases run against the same daemon, the same built worker image
and the same seams — a change that broke the accepted arc breaks these too.

### What was composed

`tests/manager/test_ended_runtime_adoption.py`. The reference worker starts,
reads its launch document, finds EOF on a closed stdin and exits — so an
exited-but-present container is the ORDINARY shape here rather than something
this suite has to manufacture.

- a restart over the same durable store adopts the exact ended runtime as
  `quiescent` — not `running`, which a `ps --all` listing alone would say, and
  not `absent`, which an empty one would. The engine still holds it: adoption
  observed and removed nothing.
- an exited container does not admit a replacement. A runtime object that
  exists is a process domain that exists, and the lane is not reusable.
- exited-but-present does not satisfy cleanup: no receipt, so cleanup blocks
  on intake and the engine is not reached at all.
- the whole ordering across a restart: adopt, take custody, force-remove,
  OBSERVE absence, settle both delivered roots — and only then a clean
  settlement, with the container gone from the daemon and both roots gone from
  disk.
- an observation the adapter cannot make never releases the lane: the axis
  records `uncertain`, cleanup settles nothing, the container is still there
  and a replacement is still refused.

### Two of my own expectations were wrong, and the code was right

**The frozen asymmetry sits BELOW the intake-receipt check.** I asserted
`authorize_cleanup` refuses `quiescence-unknown` for an uncertain runtime. It
blocks on intake first, because an attempt with no receipt never reaches that
rule. Asserting the refusal would have been asserting one this state cannot
reach; the case asserts what IS true — nothing was released.

**A mismatch is not writable here, and that is a finding rather than a gap.**
I wrote a case that edited `attempts.runtime_id` after the restart and
expected reconciliation to cancel. It answers `attached`, and it is right to:
`_attach` is effectively-once on `attempt.attach:{attempt}:{runtime}`, so the
attachment the FIRST incarnation committed replays and the compare-and-swap
never runs. The state my case built — a journalled attachment whose row was
edited behind the manager's back — is one no sequence of manager operations
produces. Keeping it would have been testing my own UPDATE, so it is removed
and the reason is written where the case was. The reachable disagreements are
covered where they ARE reachable: multiplicity by W6636's stranger case
against a real daemon, and attempt/runtime mismatch at `_attach`'s own
boundary in `test_attempts`.

### Gates

- `tests.manager.test_ended_runtime_adoption` — 5 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel source — **6 failures**, every one in
  `test_boundary_inventory` and none this Work's
- serial registry — **120 tests, 0 failed, 8 skipped**

Registered as the seventh serial module with the registry's own guard updated:
it asks the daemon whether an exact ended container is still there, which a
concurrent suite removing containers would answer for it.

## State

The restart slice is composed. Passed back for independent review rather than
closed. Podman skips narrowly because no daemon is present on this host, and
this Work does not claim it.

## 2026-08-28 — the three [P1]s, corrected

Reclaimed W32385 at seq 32568. No Git history or index was mutated.

### All three were one shape, and the review named it

Each case asserted the FINAL STATE and called it an ordering, a bound and a
reuse. A final state cannot be any of those:

- **the ordering** is satisfied by a teardown that ran BEFORE absence was
  proved — which is the process-domain invariant this Work was split out to
  preserve. One shared trace is now written by the engine's remove/inspect
  boundary and by BOTH provider teardowns, and the order is compared rather
  than the outcome. Measured, not assumed:
  `['force-remove', 'observe', 'credentials', 'launch']`, with every
  comparison non-trivial.
- **the bound** was never tested, because nothing constructed an unrelated
  attempt. A cleanup deleting by a broad label, or by the credential HOME
  rather than the exact attempt, would have passed. A sibling credential root
  now lives in the SAME assignment-scoped home — where a broad cleanup would
  reach — and it survives reconciliation, destruction and settlement with its
  live bearer intact.
- **the reuse** was never attempted, so a manager that permanently refused it
  would have passed. A real second attempt is now offered, claimed, activated
  and STARTED after the crossing: zero replacements permitted before it,
  exactly one after.

### Gates

- `tests.manager.test_ended_runtime_adoption` — 5 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's; serial registry — **120 tests, 0 failed, 8 skipped**

## State

The three findings are corrected and the ordering is measured. Passed back.

### On the acceptance's mismatch and multiplicity members

The previous round delegated them and the review refused that, correctly. They
are not added here either, and this is the honest reason rather than a second
delegation: at THIS seam an attach for the exact `(attempt, runtime)` pair has
already been journalled by the first incarnation, so the effectively-once
replay answers before any compare-and-swap runs — which is why my mismatch
case constructed a state no manager operation produces. Making mismatch and
multiplicity reachable after an ENDED-runtime restart needs a second candidate
container carrying the same labels at restart time, which is constructible;
I did not get to it this round and am not claiming it. It is the one
acceptance member still open.

## 2026-08-28 — the last acceptance member, closed

Reclaimed W32385 at seq 32646. No Git history or index was mutated.

Three cases, all reachable at this seam, and the delegation the previous round
attempted is withdrawn:

- **multiplicity at the ended restart** — a second real container carrying the
  assignment's labels, discovered by a restart beside the exact ended target.
  The manager cancels rather than choosing, and removes NEITHER; the engine is
  asked and holds two. Measured before it was pinned: `cancel`, "2 runtimes
  carry this assignment's labels", axis `cancel-requested`, two containers.
- **a sibling RUNTIME, not only a sibling root.** The previous round proved a
  sibling credential root survives; a cleanup removing containers by a BROAD
  label would still have passed that. A real sibling container under a
  different attempt's labels now outlives the target's whole crossing and is
  still `running` afterwards.
- **the reachable identity disagreement** — the adapter answering the destroy
  about a different runtime, refused `identity-mismatch` with cleanup left
  `pending`.

**And the originally worded mismatch is superseded in `FINDING.md`**, naming
the exact evidence that replaces it, because the review is right that a code
comment does not change acceptance.

### Gates

- `tests.manager.test_ended_runtime_adoption` — 8 cases, 1 narrow Podman skip,
  green against Docker 29.1.3
- full v12 parallel — **6 failures**, all `test_boundary_inventory`, none this
  Work's; serial registry — **123 tests, 0 failed, 8 skipped**

## State

Every acceptance member is now either proved here or explicitly superseded in
`FINDING.md` with its replacement named. Passed back for independent review.
