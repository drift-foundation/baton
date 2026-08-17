# Plan

**Status — 2026-08-17:** confirmed and queued after the message-pane navigation
correction to avoid overlapping command/focus state edits.

1. Revalidate the command editor and current selected-Thread/local-selector
   model after W76.
2. Seed `thread=<selected>` exactly once on contextual `say`, keeping the
   buffer editable and the caret ready for the next operand.
3. Preserve explicit paste, quoting, assist, batch mode, cancellation, and
   read-only navigation semantics.
4. Add pure and PTY tests for contextual/non-contextual entry, multiple
   Threads, selection changes, refresh/resize, duplicate prevention, posting,
   and packaged parity.
5. Run focused tests and `just test-v11`; return for independent review.
