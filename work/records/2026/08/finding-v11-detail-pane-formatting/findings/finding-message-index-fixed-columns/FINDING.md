# Finding: Message index fields drift between rows

## Observed

`WorkTUI._paint_index()` currently concatenates `M<seq>`, author address,
`HH:MM`, and personal `new`/`seen` state into one string. Different identity
lengths move the time and state fields, making rapid scanning unnecessarily
difficult.

## Confirmed decision — 2026-08-18

Render the Message index as a fixed-column table with stable Message id,
author, event time, and personal state columns. One compact header identifies
the fields. The author cell follows the configured compact team/member display
contract and is clipped inside its own allocation; it never pushes time or
state sideways. At narrower widths, a deterministic responsive layout omits a
whole lower-priority column while Message id and selection remain visible.

Newest-first display, selected-row reverse video, bold personal-new rows,
`Messages (total/unseen)`, paging, seen-through-selected behavior, focus,
scrolling, and the selected Message reader are unchanged.

## Implementation checkpoint — 2026-08-18

The accepted compact headings are `Id`, `From`, `Time`, and `St`, matching the
TUI's initial-capital header convention. `From` renders the canonical compact
`team.member` handles: each handle is already limited to six display cells, so
the complete address allocation is thirteen cells.

The Message-id allocation is computed from the longest visible `M<seq>` on the
bounded page and never clips that local selector merely because its sequence
crossed a decimal boundary. All rows on that paint use the same allocations.
Column priority is `Id`, `From`, `St`, then `Time`: the normal visual order is
`Id From Time St`, but responsive omission drops `Time` first while retaining
the viewer's personal new/seen fact. If an extremely narrow region needs to
drop more, it removes whole fields in reverse priority; `Id` and the selection
cue always survive. No field's overflow is allowed to move a later field.

W228 (`finding-message-list-obligation-cue`) is a separate follow-up. W49 must
leave a clean column-layout seam for its future viewer-relative action cue,
but does not implement or infer obligation state.
