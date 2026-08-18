# Finding: show owed actions in the Message list

## Status

Confirmed TUI usability defect on 2026-08-18. No implementation has started.

## Observed

When a Message creates a pending obligation for the viewer, the Work list and
global header expose only indirect aggregate cues such as `oblig:1`, bold Work,
and `Msg/My 2/1`. Inside the Message list, the row for the responsible Message
does not say that the viewer owes an action, identify the obligation, or name
the terminal actions that can satisfy it.

The viewer must leave the TUI or already know to run `obligations`, correlate
the returned sequence with a Message, and construct `respond`, `accept`, or
`dispose`. That makes an ordinary directed decision look like passive prose.

## Confirmed behavior

The Message list must make a pending obligation owed by the current viewer
visible on the exact Message that created it.

- The cue is personal: another member's obligation does not mark the row as
  owed by this viewer.
- It identifies the obligation by its local sequence and conveys that action
  is required; aggregate Work/header counters remain summaries, not the only
  discovery mechanism.
- Selecting the row exposes the allowed terminal actions (`respond`, `accept`,
  and/or `dispose`) and enough command context to act without consulting JSON.
- Resolved, cancelled, or superseded obligations cease to look actionable
  after refresh while remaining visible in history.
- The cue composes with the fixed-column Message index, newest-first ordering,
  personal New/seen state, narrow layouts, and keyboard focus/navigation.
- Presentation does not invent an obligation from a directed Message alone;
  canonical pending obligation state is the only authority.

The exact compact label or glyph is an implementation/UI review choice, but it
must be legible without relying on color, blink, or bold alone.

## Acceptance boundary

Cover one and many pending obligations, foreign obligations, resolution by
each allowed terminal action, refresh, narrow widths, selection retention, and
JSON/TUI parity. The fix must not change obligation authority or Message seen
semantics.
