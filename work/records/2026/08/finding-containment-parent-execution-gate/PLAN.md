# Plan

1. [done] Reproduce the contradiction between the durable containment contract
   and current readiness/phase behavior.
2. [done] Revalidate every consumer of `ready`, the displayed-gate machinery,
   both child-creation paths, terminal closure, event episodes, projection
   wording, and the tests that encode the superseded rule.
3. [done 2026-08-21] Add parent-claim/open-child, late-child, terminal-refusal,
   dependency/obligation composition, event-episode, and projection
   regressions from the matrix in `FINDING.md`.
4. [done 2026-08-21] Implement and run the complete v11 gate. One departure
   from the pinned boundary: the change DOES require a schema rollover
   (26 -> 27), for a reason the revalidation did not consider. See
   `PROGRESS.md`; this is the one decision awaiting the reviewer.
5. [done 2026-08-21] Independent review. The focused containment,
   dependency, obligation, navigation, race, workflow, soak, and schema suite
   passes 222/222. Schema 27 is approved under the explicit supersession in
   `FINDING.md`; review is recorded in
   `review-2026-08-21T14-31-41Z.md`.
