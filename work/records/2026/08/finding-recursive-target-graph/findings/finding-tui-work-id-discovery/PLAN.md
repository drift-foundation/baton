# Plan

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
