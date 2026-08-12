# Plan — TUI scoped-notice audience picker

1. Record the exact-participant ruling — **done 2026-08-11**. Notices offer `*`
   and configured `team.*` scopes only; exact participants remain directed
   messages.
2. Revalidate the parent scoped-audience ruling and current TUI picker/draft
   model in the next-generation workspace — **done by implementer**.
3. Add driver-level failing regressions for typing/filtering `lang`, manually
   submitting `lang.*`, explicit `*` global choice, absence of exact
   participants, combobox cancellation/no writes, scope-visible confirmation,
   and config-change refusal with draft preservation — **done**.
4. Add state/render coverage for deterministic filtered suggestions, manual
   valid scopes absent from suggestions, deep prefixes, deduplication,
   narrow-terminal behavior, and draft restart/reopen — **done**.
5. Implement the smallest editable picker/combobox generalization or dedicated
   audience mode that keeps directed recipients exact and submits notice
   scopes to the core unchanged — **done**.
6. Pass the selected value as `scope` to `Store.send_notice`; never expand it
   in the TUI and never fall back to global after a refusal — **done**.
7. Run focused TUI/core scope tests, the full next-generation suite, and an
   independent human-console trial before review handoff — **done**.
8. `baton.implementer` creates and owns `PROGRESS.md` when this queued item is
   started. It does not interrupt the current serial finding — **created**.
9. Repair the 2026-08-11 review blocker: persist and validate a notice draft's
   audience, restore it across restart/reopen without breaking existing
   scope-less version-1 drafts, and prove a reopened `web.*` draft cannot
   publish globally — **done; independently verified**.
10. Make the post-send status name the actual scoped audience, clear audience
    state at completed/cancelled lifecycle boundaries, add retained/reopen and
    external-editor regressions, update `PROGRESS.md` to the real review state,
    and return for review — **done; independently verified**.
11. Repair the second-review compatibility blocker: write a new draft document
    version whose notice schema requires the audience; explicitly migrate
    historical version-1 notice drafts to `*`; and prove the frozen 1.0 console
    refuses a new scoped-draft file instead of reopening it globally —
    **done; independently verified and signed off 2026-08-11**.
