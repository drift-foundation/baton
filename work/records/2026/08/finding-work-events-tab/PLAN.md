# Plan

Tracked as v11 Work W123. This is independent follow-up usability Work and is
not a dependency of the completed v11 communication capability trial.

1. [done] Revalidate the current authority and define one bounded
   `work-events work=WORK` projection over the immutable ledger. Use an
   explicit per-kind association matrix; return `roles`, related Works,
   references, and the unchanged authoritative event identity. No schema
   change or authority reinitialization.
2. [done — independently re-reviewed 2026-08-17] Proof-row paging and
   closed claim intervals are implemented. Add the required ongoing elapsed
   duration for an open claim without allowing heartbeats to reset its start.
3. [done — independently re-reviewed 2026-08-17] Add Messages/Events tabs to Work detail, defaulting to Messages,
   with `[`/`]` switching, an always-visible `[/] tabs` hint, preserved
   per-tab focus/selection/page/scroll state, and an `E<seq>` Events
   index/reader in wide and narrow layouts. Events opens newest-first; JSON
   pages remain canonical ascending.
4. [done — independently re-reviewed 2026-08-17] Preserve conversational `Msg`, `My`, `New`, Thread, and seen
   semantics unchanged.
5. [done — independently re-reviewed 2026-08-17] Cover the association matrix, direction-specific dependency
   summaries, short/exact/overflow/chained pagination,
   selection/refresh/resize/tab-switch stability, visible key hints, long
   rationale/payload rendering, ongoing and completed claim intervals, and
   JSON/TUI parity. Prove pure posts/seen cursor acts stay out while
   workflow-bearing message acts remain discoverable without body duplication.
   Add the missing reverse child/follow-up identity, duplicate-target,
   accept-created parent/provider, open-duration, and negative existing-provider
   regressions named by the review.
6. [done — source acceptance] The returned W123 gate was green before W159's
   later default-wait contract began changing the shared request fixtures.
   Independent re-review passed every corrected relation directly; W159 owns
   adapting the four affected request callers and restoring the full combined
   gate. Ready for live human evaluation in the next immutable candidate.
