# Re-review handoff: R1–R3 fixed, R4 does not reproduce

Three of the four corrections reproduced and are fixed with pins that fail
when the fix is removed. R4 does not exist in this tree. No protocol, schema
or agent-CLI change; the frozen boundary is intact. No Git operations.

## R1 — one viewport authority for the list

Reproduced exactly as you described. `layout_for` reserved the
overflow-indicator row unconditionally while `_inbox_pane` reserved it only on
real overflow, so at exactly-capacity the model scrolled against the smaller
height and row 0 left the screen with no `... above`.

`list_capacity(row_count, pane_lines)` is now the single authority — the
model's scrolling, both list panes and the selection styling all ask it — and
`layout_for` reports the PANE HEIGHT rather than second-guessing it.

**Writing the pins found a second half of the same bug that your report did
not cover and the first fix did not touch.** The top was clamped only to
`row_count - 1`, so it stayed wherever a smaller pane had pushed it: widen the
terminal until the list fits again and the pane still started at row 7,
drawing one message and silently omitting the seven above it. `list_top` is
that other half — you can never scroll past the point where the last row sits
at the bottom of the pane. Reproduced by resize sweep, fixed, pinned.

Pinned as you asked: capacity-2, -1, exactly, +1, +4; every cursor position at
each; MESSAGES and the Sent filter; first/last navigation at eight heights;
and a resize sweep across the boundary. The asserted property is the honest
pair — the selected row is always DRAWN, and if any row is off screen the pane
says so.

One pin needed care and is worth your attention: **the exact-fit case is
masked by the renderer's own clamp**, so a test reading only the drawn rows
passes with the model still wrong. I verified that. `test_an_exactly_fitting_
list_never_scrolls` asserts on `view_top` instead and fails immediately when
the unconditional reservation is restored.

A second care point: my first drafts assumed rows came back in send order.
Same-second sends tie and order by id, so that would have made them tests of
SQLite's ordering. Subjects are read from the model.

## R2 — the History view is gone

Removed end to end: `VIEW_HISTORY`, `VIEW_HISTORY_KEY`, the driver dispatch,
the state rows/cursor/top/refresh/open helpers, `selected_history`, the
history branches in `preview` and `_detail_lines`, `_history_row_lines`, and
`Store.list_received`. `open_received` stays — unified MESSAGES needs it for
handled inbound rows, owner-checked on the recipient.

**Correction to one expectation in your brief: there were no superseded tests
to remove.** Nothing in the suite referenced `VIEW_HISTORY`, `list_received`
or any history row. That is the finding restated rather than a quibble: the
code was unreachable AND untested, which is why nothing caught it drifting out
of agreement with the list that superseded it. The removal is green with no
other test touched.

Now pinned structurally — no module may carry a HISTORY name, the model may
not carry those attributes, the core may not carry `list_received` while
keeping `open_received` — plus a key-map pin that `h`/`l`/`[`/`]`/`H`/`L`
remain part navigation, so a future History cannot take `h` back quietly.

## R3 — outbound lifecycle in MESSAGES

Reproduced. Outbound directed rows now render through `sent_badge` for every
state, including `pending` and `claimed`. Inbound notation and action
semantics are unchanged and pinned separately so the badge cannot leak the
other way.

**One thing I did beyond the correction, declared.** Sending outbound rows
through `sent_badge` made a latent alignment fault common instead of rare: a
1-cell glyph beside a 3-cell badge shifts the date and sender two cells on
alternating rows, and after this change that is most of the list. Both list
panes now draw the status column at one width (`GLYPH_WIDTH`), with the
subject budget corrected to match. Pinned by asserting the date column starts
at the same cell across an inbound row, an outbound row and a notice. Say the
word and I will drop it, but a ragged column is what the change would
otherwise have shipped.

Regressions are on the RENDERED MESSAGES screen, as you asked — not on
`sent_badge` and not on the Sent view.

## R4 — does not reproduce

`_delivery_lines` contains `content = message.get("content") or {}` exactly
once, at one call site. A scan of `baton_tui/` and `baton_core/` for any
consecutive duplicated assignment finds none. Nothing was changed. Flagging it
rather than silently skipping it, in case you were reading a different
revision — if you can name the line number you saw it at I will look again.

## Deliberate-break checks

| Break | What fails |
|---|---|
| reserve the indicator row unconditionally again | the exact-fit no-scroll pin |
| drop the `list_top` clamp | the resize-across-the-boundary pin |
| outbound rows back through the inbound notation | the queued/picked-up pin |
| drop the common glyph width | the column-alignment pin |
| a History constant put back | the structural no-History pin |

## Verification

    just test          1578 passed   (was 1560)
    git diff --check   clean
    bin/baton-tui      b4ec0a4a9dc6462b37d93f74276edf2c352a5aa86d48772346bc5e6b79c07de6
                       deterministic: rebuilt twice, byte-identical
    frozen             bin/baton a23461ae7577422f5c4ade86eae370926b2dc41bc93ecd7732c29b2785374566,
                       DISTRIBUTION.json, baton_v6.py, build_zipapp.py unchanged
    docs               test_docs_consistency.py green

README flow executed end to end again against a temporary instance; `doctor`
reports it clean.

## Durable recovery record updated

- **PLAN.md** — status table gains R1/R2/R3, all `done, pinned`; the
  verification block carries the new test count and artifact hash.
- **TRIAL.md** — a full "R7 re-review: four corrections, three real" section:
  each reproduction, the second half of R1 that the report did not cover, why
  R2 had no tests to remove, the alignment consequence of R3, the R4
  non-reproduction, and the break table.
- **FINDING.md §3b** — two normative additions: outbound rows carry the SENT
  badge in MESSAGES for every directed state at one column width, and the
  one-viewport-authority contract (the selected row is always drawn; no row is
  hidden without the pane saying so).

## Changed paths since the last handoff

    baton_tui/render.py
    baton_tui/state.py
    baton_tui/driver.py
    baton_tui/keys.py
    baton_core/_impl.py
    bin/baton-tui
    DISTRIBUTION-TUI.json
    test_tui_render.py
    work/finding-human-console/FINDING.md
    work/finding-human-console/PLAN.md
    work/finding-human-console/TRIAL.md

New tests, all in `test_tui_render.py`:
`test_the_messages_list_never_hides_a_row_silently`,
`test_an_exactly_fitting_list_never_scrolls`,
`test_the_sent_filter_never_hides_a_row_silently`,
`test_first_and_last_are_reachable_and_drawn_at_every_size`,
`test_resizing_across_the_capacity_boundary_keeps_the_selection_drawn`,
`test_there_is_no_history_view`, `test_h_and_l_remain_part_navigation`,
`test_an_outbound_row_shows_queued_and_picked_up_in_messages`,
`test_inbound_notation_is_unchanged_beside_it`,
`test_every_list_row_aligns_whichever_notation_it_uses`, plus `_list_rows` and
`_assert_the_list_is_honest` helpers.

No existing test was rewritten in this round.

## Still outstanding, unchanged

`assets/artwork/baton-tui.png` still depicts the side-by-side columns and
needs a real-terminal capture from Slawomir's trial. Recorded in PLAN under
"Remaining before this stage is committed", with the README saying so in prose
beside the image.

References:
- baton_tui/render.py
- baton_tui/state.py
- baton_tui/driver.py
- baton_tui/keys.py
- baton_core/_impl.py
- test_tui_render.py
- work/finding-human-console/FINDING.md
- work/finding-human-console/PLAN.md
- work/finding-human-console/TRIAL.md
- README.md
- assets/artwork/baton-tui.png
- DISTRIBUTION-TUI.json
