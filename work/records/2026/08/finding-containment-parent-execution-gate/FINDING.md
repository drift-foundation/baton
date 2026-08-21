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
