# Esc from DETAIL returns to the message list

Status: **implemented and independently approved; awaiting human zipapp trial**.

Parent: `work/finding-human-console/`.

Discovery context: after the corrected packaged Enter path passed the live
trial, Slawomir proposed its directional counterpart: people should be able to
learn “Enter enters the message; Esc leaves it.”

## Confirmed interaction

In BROWSE mode:

- with DETAIL focused, Esc moves focus to LIST;
- with LIST focused, Esc does nothing;
- Enter remains the one-way LIST-to-DETAIL action;
- Tab and Shift-Tab remain the reversible pane toggle. They are not removed:
  Tab still gives symmetric keyboard traversal and can enter DETAIL without
  opening/committing a selected notice;
- focus transfer is pure UI state. It preserves the selected row, opened
  content/claim, list and detail offsets, selected part, draft state, status,
  and all authority state;
- it creates no claim, receipt, disposition, publication, reread, refresh, or
  filesystem write.

Esc retains its existing modal meaning everywhere else. In compose, reply,
recipient/root pickers, send confirmation, draft handling, and help it still
cancels, declines, or closes the active modal exactly as already documented.
This is not the exploratory Vi-mode proposal and does not introduce
Normal/Insert modes.

## User-facing boundary

The generated `?` help owns the shortcut description. Do not add a permanent
work-area hint or footer tutorial; the live trial has deliberately removed
that visual noise.

## Required evidence

1. DETAIL-focused BROWSE + Esc returns to LIST and preserves every relevant
   UI-state field.
2. The same transition is proven to make no store call, using a refusing
   store or an equally strong boundary.
3. LIST-focused BROWSE + Esc is a no-op.
4. Enter, Tab, and Shift-Tab keep their existing focus semantics.
5. Every modal Esc path keeps its existing cancel/decline/close behavior.
6. Generated help documents the browse DETAIL-to-LIST action without adding
   a permanent on-screen hint.
7. A packaged PTY regression proves Esc returns focus after Enter or dwell has
   placed the reader in DETAIL.
8. The next human handoff carries a freshly rebuilt `bin/baton-tui`.

No protocol, schema, CLI, or core change is authorized by this finding.

## Resolution

Approved by `baton.reviewer` on 2026-08-10. Browse Esc is a distinct
`LEAVE_DETAIL` event: it returns DETAIL focus to LIST, is a no-op in LIST, and
never enters the modal cancel paths. The focused model/help/PTY evidence and
an independent deterministic artifact rebuild passed. Slawomir's zipapp test
is the remaining trial gate before the final full release suite.
