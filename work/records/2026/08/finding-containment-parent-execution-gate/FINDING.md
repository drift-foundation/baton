# Finding: do not gate parent execution on open children

Canonical Baton Work: W1477.

## Observed — 2026-08-21

After parked W2 was returned to `queued`, Baton immediately changed it to
`block` with gate W1466 solely because W1466 was an open containment child.
W2 had no dependency blocker. A subsequent claim correctly refused the
blocked phase.

This contradicts the durable operator contract in `docs/EFFECTIVE-BATON.md`:
parent/child containment organizes a deliverable and prevents parent closure,
but is not an execution dependency and must not prevent the parent proceeding.

## Confirmed cause

`src/baton_work/transitions.py:_recompute_ready()` currently defines readiness
as open Work with no open children and no open dependency blockers. Its
false-to-zero path then derives the `block` scheduler phase and names the child
as a gate. The projection source also acknowledges that open children gate
readiness, despite the documented product ruling.

## Proposed correction

Separate execution readiness from terminal containment closure. Only explicit
dependency or obligation gates make an open parent unclaimable. Open children
remain visible containment, prevent terminal parent closure, and contribute to
their existing roll-up views without forcing the parent into `block`.

## Acceptance boundary

- A parent with an open child but no explicit gate remains claimable.
- The same parent cannot close until every child is terminal.
- Explicit dependency and obligation gates still block claims.
- Adding an open child does not release an existing parent claimant.
- Containment trees, message roll-up, terminal refusal, and cycle protection
  retain their current behavior.

## Revalidation — 2026-08-21

The contradiction is broader than `_recompute_ready()` but remains one
coherent behavior-only correction. No authority table or persisted field must
change, so this Work does **not** require a schema rollover.

## Supersession — 2026-08-21: persisted derivation requires schema 27

The preceding no-rollover conclusion is **superseded**. Its table-shape fact
remains true, but schema compatibility also covers the meaning of persisted
derived state. Schema 26 authorities may contain `ready=0`, `phase=block`, and
a child-valued gate episode for parents whose only supposed gate is an open
child. Under the corrected rule those values are invalid, and removing the
child-driven parent recomputation also removes the transition that might have
eventually repaired them.

The global wake sweep cannot provide a safe implicit migration: it may move
such a parent to `queued` while leaving `ready=0`, making the Work claimable by
id but permanently absent from readiness projections. Baton deliberately has
no in-place authority migration and does not guess across schema versions.
Therefore this behavior correction increments `SCHEMA_VERSION` from 26 to 27
and requires a fresh authority at deployment. A one-off backfill is rejected
for this release; fail-closed rollover is the accepted boundary.

### Confirmed implementation surface

- `src/baton_work/transitions.py:_open_gates()` currently counts children and
  dependency blockers together. Scheduler/readiness callers must count only
  live explicit dependency edges; directed-obligation blocking remains its
  existing separate gate path.
- `_recompute_ready()` currently folds `open_children` into `ready`, releases a
  live parent claim when a child appears, moves an unclaimed parent to
  `block`, and mints an assignment episode when the last child closes. Each of
  those child-driven scheduler effects must disappear.
- `_displayed_gate()` currently selects the oldest item from a union of open
  children and blockers. A Work gate displayed in `Wait` must come only from a
  live explicit dependency edge; containment remains visible in the tree.
- `_unclaimed_state()`, `_sweep_wakes()`, `claim_work()`, and manual
  `phase to=block wait=gates` all consume the aggregate gate helper. Their
  semantics remain intact once that helper means explicit dependency gates.
- Both Work-creation paths call `_recompute_ready()` for a parent after adding
  a child. They may retain a harmless recomputation or stop making it, but
  child creation must not change the parent's `ready`, `phase`, Handler, gate,
  or assignment episode.
- Terminal `close_work()` performs an optimistic and an in-lock open-child
  check. Both checks remain unchanged: containment still prevents terminal
  parent closure.
- The containment walk in cycle refusal also remains. Although containment is
  not an execution gate, terminal ordering plus an opposing dependency can
  still form a graph that cannot complete.
- `src/baton_work/authority.py`, `src/baton_work/projection.py`, CLI errors,
  and `docs/EFFECTIVE-BATON.md` contain child-gate wording that must be made
  consistent with the already-pinned containment contract. The existing
  schema can still represent dependency (`work`) and obligation (`message`)
  gates without modification.

### Regression matrix

Positive cases:

1. An unclaimed parent stays `queued`, ready, gate-free, and claimable after a
   child is created.
2. A claimed parent keeps the same Handler and active assignment episode when
   its authorized Handler creates a child.
3. Closing one or the last child changes containment progress but does not
   create a parent wake, gate episode, or assignment episode.

Negative and composed cases:

1. Closing a parent with any open child still refuses by naming the children,
   including the in-lock race check.
2. An explicit dependency still releases a claimant, moves the consumer to
   `block`, appears in `Wait`, refuses a claim, and wakes exactly once when the
   last dependency clears.
3. A blocking directed obligation retains its typed Message gate and wake.
4. A parent with both open children and a live dependency is blocked only by
   the dependency; clearing it makes the parent runnable even while children
   remain open.
5. Tree depth/disclosure, breadcrumb navigation, recursive message counts,
   terminal roll-up, and union-graph cycle refusal retain coverage.

The tests that intentionally encode the superseded rule include
`test_transitions.py`, `test_edges.py`, `test_w49_assignment_episodes.py`,
`test_w47_event_phase_intervals.py`, `test_w78_typed_timed_gates.py`,
`test_tui.py`, `test_parity.py`, and workflow `test_wf06.py`. They must be
rewritten to assert the confirmed distinction, not simply deleted.
