# Plan

**Status — 2026-08-16 11:42Z:** active with `baton.implementer` in the
pre-cutover cleanup batch; live W12 was passed to `baton.impl` at authority
sequence 156 and returns next to `baton.bug`. The later short-selector ruling
has resolved the interaction question; this item requires no fresh authority.

1. Revalidate every TUI command requiring a Work id and inventory where the
   current TUI exposes—or fails to expose—the selected Work identity.
2. Propose the smallest exact, discoverable interaction for retrieving or
   targeting the selected Work without relying on unique titles, transient
   status, hidden selection, or guessed sequence numbers.
3. Add real-screen and command-bar regressions for creation followed by missed
   output, later ID recovery, narrow terminals, duplicate titles, scrolling,
   and selection changes.
4. Implement only after the interaction is reviewed; preserve canonical JSON
   ids and all authorization/effectively-once boundaries.
5. Run focused coverage and `just test-v11`, then return for review before the
   next immutable v11 distribution.
6. Remove W12 from the fresh-authority recreation inventory and update its
   counts/proof after verification.

**Closed satisfying — 2026-08-16 11:49Z.** Final review is clean at
`review-2026-08-16T11-49-51Z.md`; the live Work closed at authority sequence
160. The implementation reports 642 parallel plus 3 serial tests green, and
the focused duplicate-title/narrow-width PTY target and final diff check pass.
W12 is removed from W92's recreation set. Deployment remains held by the
continuing pre-cutover audit and its other same-schema corrections.
