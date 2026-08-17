# Plan

**Status — 2026-08-17:** signed off in
`review-2026-08-17T00-03-17Z.md`; focused and complete v11 gates are green.
W176 may close satisfying and unblock W187.

## Revalidation — 2026-08-16

- `_render_detail()` currently places the lower region immediately after the
  last painted Thread row. Reserve exactly one blank row before invoking the
  message-region renderer; retain the existing bounded Thread-list budget.
- `_render_message_region()` currently derives `Msgs — <subject>` and `»M…`
  from the selected Thread/Message. Replace those with stable pane-role labels
  `Messages (N)` and `Message M…`; the Thread row remains the sole subject
  owner and the reversed message-index row remains the selection cue.
- Keep the current wide split and narrow stack. Both arrangements need honest
  empty/one/many counts and must preserve the footer/control row.
- Supersede the old assertion in
  `test_the_msgs_pane_names_the_selected_thread_and_subject`; add focused wide,
  narrow, long/wide-subject, empty, one-message, multi-message, selection, and
  exact-separator coverage without weakening unrelated navigation tests.

1. Revalidate the current split-pane geometry and narrow-width behavior.
2. Replace the content-repeating message heading with stable `Messages (N)`
   and `Message M…` pane labels, separated from the Thread list by one blank
   row.
3. Keep Thread subjects in Thread rows, message selection in the list, and
   message metadata separate from the body.
4. Add virtual-screen coverage for empty, single, multiple, long-subject,
   wide-character and narrow-terminal cases.
5. Run the complete v11 gate and return for independent visual/code review.
