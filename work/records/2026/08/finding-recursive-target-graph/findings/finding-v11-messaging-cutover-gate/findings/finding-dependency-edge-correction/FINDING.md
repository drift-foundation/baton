# Finding: mistaken dependency edges cannot be corrected

## Observed — 2026-08-17

W76, W81, and W90 were added as blockers of W2 while W2 was interpreted as an
umbrella for all remaining messaging-interface work. Slawomir subsequently
clarified that W2 is the capability gate for replacing v10 and that these three
open usability items are independent follow-ups.

The deployed protocol exposes `block work=... on=...` but no authoritative
inverse operation. Dependency rows therefore remain live until the blocker is
terminal. The authority correctly refuses to close W2 while those open edges
remain. Raw SQLite edits are prohibited and would destroy the audit contract;
closing or cancelling unfinished blockers merely to clear their edges would
falsify those Work outcomes.

## Confirmed requirement

Add an append-only dependency correction operation. The Current handler of the
consumer Work may deactivate one exact live `work`/`on` edge with a required
rationale. Adding a dependency must likewise require a rationale: both acts
change what may proceed, so both are reviewable decisions rather than bare
graph mechanics. The event ledger must retain the original addition and the
correction; canonical projections and readiness use only live edges.

**Superseded later on 2026-08-17:** the initial direction to put dependency
events in Messages conflated conversation with workflow history. Slawomir
approved a separate Events tab instead; the durable decision is recorded in
`work/records/2026/08/finding-work-events-tab/`.

Both dependency events appear in each affected Work's Events view with actor,
time, the related Work, and rationale. They remain typed workflow-journal
events—not forged Thread discussion messages—and a human must not need the raw
event API to discover why a dependency appeared or vanished.

The operation must:

- fail closed unless the exact live edge exists;
- use the consumer Work's Current-handler authorization;
- recheck Work and edge state inside the committing transaction;
- recompute readiness atomically and mint the ordinary unblock assignment
  episode when the last gate is removed;
- be effectively-once through `op-id`;
- preserve historical graph evidence rather than deleting the original event;
- project both addition and correction as readable entries in each affected
  Work's Events view;
- leave both Work items and their contracts otherwise unchanged.

This correction is required to apply the confirmed W2 boundary honestly. It is
not a general mechanism for bypassing unfinished dependencies: the required
rationale and durable event make the correction reviewable.
