# Plan

1. Revalidate the priority contract against the current authority schema,
   event ledger, projections, CLI/TUI parity, authorization, and retry model.
2. Add required canonical Work priority with values `high`, `normal`, and
   `low`; creation defaults to `normal`.
3. Add an audited, effectively-once priority revision authorized to members of
   the owning team. Refuse cross-team mutation without changing authority.
4. Expose full priority in JSON and compact `Pri` values `High`, `Norm`, `Low`
   in the TUI. Order otherwise comparable Work by priority, then preserve the
   existing stable canonical tie-breaker.
5. Add positive, default, authorization, retry, restart/rebuild, ordering, and
   TUI/JSON parity regressions proving that priority never mutates workflow
   readiness, dependencies, ownership, phase, or status.
6. Run focused coverage and `just test-v11`, then return for review before the
   next immutable v11 distribution.
