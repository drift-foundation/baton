# Plan — TUI bulk selection and trash

1. **Pin inclusion** — **superseded 2026-08-12**. The 2026-08-11 requirement
   to ship bulk select/trash in Baton 1.1.0 is retained as history, but no
   longer actionable.
2. **Rule trash lifecycle** — **done 2026-08-11**. Slawomir clarified this is
   recoverable Inbox archiving for visual cleanup; authority rows/content stay
   exactly retained and protocol deletion/lifecycle acts are out of scope.
3. **Rule persistence and compatibility** — **superseded 2026-08-12**. The
   participant-local versioned JSON design under `projection_dir` must not
   ship. Slawomir ruled SQLite is the metastore owner, requiring protocol 11.
4. **Finish the interaction contract** — **done 2026-08-11** in `FINDING.md`:
   MESSAGES/Archived/Sent behavior; exact eligibility; Space/Ctrl+A/U/x;
   fixed identities; refresh/filter/view lifetime; marks/counts; atomic local
   persistence; restore and stale-id behavior. Slawomir additionally confirmed
   that archived entries remain searchable through the metadata-only `/`
   filter in the Archived view.
5. **Withdraw the protocol-10 implementation** — **done 2026-08-12**. K removed
   the participant-local JSON archive store and
   its 1.1-only UI/help/tests, preserving independently approved shared 1.1
   work. K exclusively owns `PROGRESS.md`. Do not modify frozen 1.0 artifacts
   or manifests, live authority/config, deployment, or Git state.
6. **Verify the withdrawal** — **done and approved 2026-08-12** in
   `review-2026-08-12T05-26-19Z.md`. The archive file/module, view,
   browse keys, help/count surface, and focused/PTY archive cases are absent;
   run the affected TUI tests and full repository suite. Existing protocol-10
   behavior and every separately approved 1.1 feature must remain intact.
7. **Advance 1.1** — **cleared 2026-08-12**. Withdrawal and included-finding
   reconciliation are approved. Bulk archive is no longer a human-soak or RC
   gate; tell Slawomir the 1.1 candidate can proceed to human testing/RC.
8. **Design protocol 11** — queued. Add participant-scoped archive metadata to
   the SQLite metastore, revalidate the retained UX/safety decisions against
   that schema, and define migration, transactional bulk operations, and
   compatibility before implementation.
