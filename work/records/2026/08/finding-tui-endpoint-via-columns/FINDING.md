# Finding: distinguish Endpoint from Via in Work lists

## Observation — 2026-08-18

The Work table labels one column `Route`, but its cells render
`row["route"]["endpoint"]`. For implementation Work that cell is
`baton.impl`, regardless of whether the authority selected default route
`impl` (Claude) or alternate route `impl2` (Gemini).

Before alternate routes this mismatch was mostly terminological. With W230 it
is operationally misleading: the column says Route while hiding the actual
route that determines eligibility.

## Confirmed vocabulary and presentation

- **Endpoint** is the stable `TEAM.KIND` address, for example `baton.impl`.
- **Via** is the selected internal route, for example `impl` or `impl2`.
- **Handler** is the exact participant after a successful claim, for example
  `baton.gemini`.

The Work table renames `Route` to `Endpoint` and adds a compact `Via` column.
Before claim, Endpoint + Via states exactly where the Work is offered; after
claim, Handler confirms who actually took it. JSON keeps the already explicit
structured route object and does not encode this distinction through column
labels or glyphs.

Responsive omission may drop Endpoint and Via before Handler at narrow widths,
but it must drop whole columns rather than truncate identities into ambiguity.
Endpoint and Via must never disagree with the selected route used for claim
authorization.

## Acceptance boundary

Add focused default-route, alternate-route, claimed/unclaimed, unresolved
route, terminal-row, and responsive-width rendering tests. Assert that
`baton.impl` appears under Endpoint, `impl2` under Via, and `baton.gemini`
under Handler for a claimed alternate-routed Work. Run the complete v11 gate.

