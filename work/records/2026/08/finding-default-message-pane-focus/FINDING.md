# Focus Messages when opening Work details

## Observed — 2026-08-20

Opening a Work currently selects its first discussion Topic but leaves keyboard
focus in the Topics pane. Most Work has one primary Topic, so reading or acting
on its Messages requires an extra `Tab` or `Ctrl-W j` before the operator can
move through the Message index.

## Confirmed decision

- Work detail continues to open on the Messages tab and continues to select the
  first Topic using the existing new-first/default selection rule.
- Initial keyboard focus lands in that Topic's Message index, not in the Topics
  pane. The visible Topic selection still determines which Messages are shown.
- This default applies consistently when Work detail is entered from Jobs,
  search results, or Inbox context.
- Topic navigation remains directly available through pane navigation; this is
  a default-focus change, not removal of the Topics pane.
- Empty Work and an empty selected Topic remain safe and navigable. Defaulting
  to the Message index must not invent a Message, mark anything seen, or mutate
  authority state.
- Returning to an already-open detail view preserves the established per-view
  focus where applicable; the new default is for a fresh detail entry.

## Acceptance boundary

- Opening a Work with one Topic and Messages highlights/focuses the Message
  index immediately; `j`/`k` operate on Messages without a preliminary pane
  switch.
- The same behavior is covered from Jobs, search, and Inbox entry paths.
- Multi-Topic Work still selects the existing default Topic, and the operator
  can move to Topics with `Shift-Tab` or geometric `Ctrl-W` navigation.
- Work with no Topic and Topics with no Messages render without error and allow
  focus to leave the empty Message pane.
- Entry changes no seen cursor, selection authority, Message state, or Work
  state.

