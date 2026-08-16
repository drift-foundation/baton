# TUI finding — opened detail state falls behind the selected list row

**Status:** confirmed by Slawomir's packaged-console trial on 2026-08-10;
unreviewed implementation work for the current TUI candidate.

## Observed behavior

1. Open a message so the lower detail pane renders its lifecycle metadata,
   including `State:`.
2. Leave that same row selected while the other participant changes the
   underlying message state.
3. The periodic poll refreshes the top list: its glyph/state changes.
4. The lower detail pane continues to show the old `State:` value.
5. Navigate away from the row and back. The detail then shows the current
   state.

The two panes therefore contradict each other for the same selected message.
The polling path is demonstrably seeing the authority change; only the opened
detail snapshot is stale.

## Likely boundary to inspect

`InboxState.refresh()` rebuilds `rows` from `list_messages()` and
`_refresh_sent()` rebuilds `sent_rows` from `list_sent()`. Selection is restored
by stable identity, which is correct. But an already opened detail remains a
separate envelope in `self.detail`. For an outbound row,
`open_sent_selected()` / the outbound branch of `open_selected()` captured the
old `sent` envelope, and `_sent_content_lines()` continues rendering that
snapshot until the row is reopened.

This is a hypothesis to verify, not authority. The same audit must cover an
opened received/claim envelope and notices so the fix does not merely move the
contradiction to another detail shape.

## Required behavior

Keep `State:`; it is useful exact protocol information. Synchronize lifecycle
metadata for the opened detail whenever the read-only poll observes a newer
row for the same stable identity. The list and detail must render one coherent
authority snapshot after a refresh without requiring navigation.

- Matching is by row kind and stable message/notice ID, never cursor index.
- Polling remains observational: no claim, receipt, disposition, materialize,
  or content redelivery is introduced.
- Do not replace retained content bytes merely to update metadata. A notice
  body already delivered at most once must not be requested again, and an
  external/damaged part must not cross a new authorization boundary.
- Preserve detail part selection, vertical/horizontal offsets, focus, draft,
  and active action target when the same row remains selected.
- If the current claim becomes terminal or is replaced, the existing
  `_revalidate_action_target()` safety behavior remains authoritative: stale
  actionable ownership must be dropped rather than cosmetically relabeled.
- If a row disappears, keep the existing explicit unavailable behavior; do
  not silently attach the detail to the row now occupying the old index.

If one refresh cannot obtain both list and detail metadata coherently, retain
the prior coherent pair and label the refresh failure. Do not combine a fresh
list state with known-stale detail state.

## Required regressions

- opened outbound pending -> claimed updates list glyph and detail `State:` on
  the same poll, without navigation;
- opened outbound claimed -> completed/closed does the same;
- identity is preserved when a newer arrival reorders the list;
- another row changing never updates the selected detail;
- an opened active inbound claim does not lose content, part selection,
  offsets, focus, or action target during a metadata-only refresh;
- a terminal/replaced claim still drops stale actionable ownership;
- an opened seen notice is not redelivered to synchronize activity metadata;
- refresh failure never produces a deliberately split list/detail snapshot;
- packaged zipapp/PTY coverage proves the visible list glyph and detail state
  agree after the background polling interval.

## References

- `baton_tui/state.py`
- `baton_tui/render.py`
- `baton_tui/driver.py`
- `test_tui_state.py`
- `test_tui_render.py`
- `test_tui_pty.py`

## Review 1 — changes requested

The directed SENT-message correction is sound and its focused regressions
pass. The metadata boundary is explicit, identity-based, and does not replace
content or disturb the reading position.

The same-class notice path is still omitted. `open_sent_selected()` stores an
authored notice under `self.detail["sent_notice"]`, but
`_opened_envelope()` recognizes only `delivery`, `sent`, `received`, and
`notice`. Consequently the new `seen_count` and `expires_ts` entries in
`_SYNCED_FIELDS` are unreachable for the authored-notice detail shape: the
SENT list can update while the opened detail remains stale, exactly as the
directed message did.

Teach `_opened_envelope()` the `sent_notice` envelope (or otherwise route it
through the same metadata-only identity sync). Add the authored-notice
regression the original finding required: open the author's SENT notice,
record another participant's receipt, refresh, and assert list and detail
`Seen by` metadata agree without calling `open_sent_notice` again or replacing
the retained content. Then rerun the focused state/render tests. No redesign of
the accepted directed-message path is requested.

## Review 2 — `sent_notice` is covered; partial-refresh coherence is not

The `sent_notice` envelope and authored-notice regression now cover the missed
shape, and all seven focused sync tests pass. The source-derived envelope-key
tripwire is a useful guard against adding another rendered opened shape without
sync support.

One original acceptance boundary is still violated. The implementation applies
matching `rows` and then matching `sent_rows`, with SENT metadata always
winning. `_refresh_sent()` deliberately keeps its old cache when `list_sent`
fails. Therefore this sequence is possible:

1. an outbound message is opened from the primary Messages view;
2. `list_messages()` observes its new state successfully;
3. `list_sent()` fails, so `sent_rows` remains the older snapshot;
4. `_sync_detail_metadata()` copies the fresh primary row, then overwrites it
   with the stale SENT row because SENT is applied last.

The visible Messages glyph is fresh while detail `State:` is stale again. This
is exactly the split-snapshot failure the finding says must not be created.
The richer-SENT precedence is correct for an opened authored notice, but it is
not a generally valid precedence across independently guarded reads.

Choose the metadata source that owns the opened view/shape (the stable
`detail_row` kind already distinguishes a SENT preview/open from a primary-list
row), or carry refresh success/generation explicitly and only merge snapshots
known to belong to the current poll. Add a regression where the primary list
advances, `list_sent` fails, and a primary-list opened outbound detail remains
coherent with the primary row. The symmetric SENT-view case must retain its
prior coherent SENT list/detail pair. Do not remove stale-but-labelled failure
handling to make this pass.
