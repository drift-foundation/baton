# Finding: Work that blocks the team needs derived urgency

## Observation — 2026-08-18

W5 appeared stuck even though its own implementation route was idle. The live
chain was W5 contains open W6, and W6 waits on W101. W101 was implemented,
ready, and unclaimed on the single reviewer route. Its ordinary queue position
therefore held W6, W5, and the Tuner-facing documentation track even though
nothing in W101's displayed priority communicated that fan-out.

A multi-agent system can stall the team when one route processes isolated Work
before a ready defect that gates several other participants. Manually changing
the blocker's priority loses the owner's original ordering decision and goes
stale as dependencies open and close.

## Proposed scheduling model

Keep the owning team's explicit `high | normal | low` priority unchanged and
auditable. Derive a separate **effective urgency** for scheduling and
presentation:

1. A Work inherits the highest explicit priority among its live transitive
   dependents, including parents held open by containment.
2. At equal effective priority, the number of live downstream Work items is a
   deterministic tie-breaker; a blocker releasing more of the pipeline goes
   first.
3. Stable creation order remains the final tie-breaker.
4. Closing, unblocking, or otherwise satisfying an edge removes its influence
   immediately. No automatic operation rewrites the Work's explicit priority.
5. JSON exposes stated priority, effective priority, live downstream count,
   and the reason/source of any boost. Clients never infer the boost by parsing
   a TUI glyph.
6. Home/tree/search ordering and participant-action readiness use the same
   canonical effective ordering, so a bridge and a human see the same next
   Work.

The compact TUI must distinguish stated priority from a derived boost rather
than silently replacing `Pr`. The exact display spelling remains a design
decision.

## Acceptance questions

- Confirm whether containment parents contribute exactly like dependency
  consumers; the W5/W6/W101 case argues that they must.
- Confirm whether fan-out is direct or transitive; team unblocking requires a
  transitive count without double-counting shared downstream Work.
- Define how a parked downstream item affects urgency.
- Prove deterministic behavior for chains, diamonds, mixed priorities,
  satisfied edges, closed Work, filters, and multiple routes.
- Keep the computation bounded for the two-second TUI refresh and readiness
  polling paths.

