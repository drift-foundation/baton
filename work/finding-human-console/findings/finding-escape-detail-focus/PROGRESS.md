# Progress

Owner: `baton.implementer` only.

## 2026-08-10 — implemented

State: **complete, pending review.** 2289 passed. `bin/baton-tui` rebuilt.

`Esc` is bound in browse mode to a new `LEAVE_DETAIL` event -- separate from
`TOGGLE_FOCUS` because it is one-way, and separate from `CANCEL` because it
cancels nothing. One name for two meanings is how a key ends up doing the
wrong one, and Esc already has five modal meanings to keep clear of.

`InboxState.leave_detail()` sets focus to LIST and does nothing else. It
returns early outside browse mode, so the modal paths are untouched.

The dispatch is UNGATED by the affordance query, deliberately: Esc is a no-op
in LIST by contract, and routing it through that query would make the console
report "unavailable" for doing exactly what it is supposed to do there.

Evidence 1-7:

1. Esc from DETAIL returns to LIST, and a second test asserts the cursor,
   both offsets, the part cursor, the opened claim, the status and the
   selected row are all unchanged -- a focus move that quietly reset any of
   those would be a different operation wearing the same key;
2. proved with a store that RAISES on any attribute access, so "no store
   call" is a fact rather than a claim;
3. Esc in LIST changes nothing at all, asserted field by field;
4. Enter still one-way in, Tab still reversible both ways;
5. Esc still cancels a modal flow;
6. the generated help documents it. The existing
   `test_the_help_lists_every_active_browse_binding` FAILED until I added the
   entry, which is the guard working exactly as intended -- I did not have to
   remember;
7. a packaged PTY regression. That one earns its place: Esc arrives as a bare
   `\x1b`, which is also the prefix of every arrow-key sequence, so only a
   real terminal proves the key is delivered as Esc rather than swallowed
   while the reader waits for a sequence tail.

Break-checked: removing the binding fails three model tests and the packaged
one; removing the browse-mode guard fails the help-coverage test.

No protocol, schema, CLI or core change, as the finding requires.
