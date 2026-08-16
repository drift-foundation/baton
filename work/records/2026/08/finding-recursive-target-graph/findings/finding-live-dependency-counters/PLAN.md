# Plan

**Status — 2026-08-15:** cancelled as a separate item and superseded by W71.
The historical steps below are not actionable. W71 preserves the canonical
JSON pair and detail/links presentation while dropping graph/progress columns
from the main Work tree.

1. Revalidate dependency creation, every terminal outcome, open-dependent
   closure, projection rebuild, links, recursive tables, responsive layout,
   and JSON/TUI parity against the two-counter contract.
2. Replace ambiguous row-only `dep` exposure with canonical
   `open_blockers` and `open_dependents`, preserving exact graph direction and
   live-only semantics. Do not add historical totals to active rows.
3. Render compact `Blk` and `Dep` columns and retain both through responsive
   layouts wherever actionable graph state is shown.
4. Add positive and inverse-direction regressions for edge creation, multiple
   blockers/dependents, satisfying/non-satisfying/rejected/cancelled closure,
   consumer closure, races, restart/rebuild, recursive views, and TUI/JSON
   parity.
5. Run focused coverage and `just test-v11`, then return for review before the
   next immutable release.
