# TUI feature — retained drafts and explicit discard

**Status:** confirmed UX requirement from Slawomir's packaged TUI trial on
2026-08-09.

## Problem

While composing a new message or a reply, pressing `Esc` twice can discard the
entire draft. Escape is a navigation/cancel key and is easy to press while
backing out of an editor. It must not also be an implicit destructive action.

## Required contract

- Leaving compose/reply editing with `Esc` retains the draft.
- A retained draft is visible and reopenable from the Messages view.
- Preserve the complete authoring state: compose kind, recipient or replied-to
  message, subject, body, and any part/reference/attachment selections.
- Retaining or previewing a draft has no Baton authority effect: it does not
  publish, claim, close, reply, mark a notice seen, or create audit state.
- A failed send retains the draft unchanged. A successful send removes only
  the committed draft.
- Draft retention should survive TUI restart; write participant-local state
  atomically with restrictive permissions and never log draft bodies. The
  storage location/format is a TUI implementation detail, not protocol state.

## Explicit discard

Uppercase `D` is the destructive action when a draft row is selected/open:

```text
Discard draft? y/N
```

- `y` or `Y`: discard the selected draft;
- `n`, `N`, `Enter`, or `Esc`: keep it;
- default is **No**;
- `D` on a non-draft message must not delete or dismiss that message.

The confirmation occupies the single status line and must not create a second
prompt line or mid-screen instructions.

## Acceptance coverage

Pin at least:

1. new-message draft survives one and repeated `Esc` actions;
2. reply draft remains tied to its original message and survives navigation;
3. both survive process restart;
4. failed send retains, successful send clears;
5. `D`, then `Enter`/`n`/`Esc`, retains;
6. `D`, then `y`, discards only the selected draft;
7. `D` cannot delete a normal message, notice, or sent-history row;
8. packaged zipapp behavior, including narrow-screen confirmation rendering.
