# Plan — TUI message search

1. **Queue the user request without interrupting release work** — completed.
2. **Revalidate available read-only row/content data** — completed.
3. **Rule search scope, matching, result navigation, and refresh behavior** —
   completed and pinned in `FINDING.md`.
4. **Implement state and rendering without claim/seen side effects** —
   completed in next-generation source.
5. **Add pure, race/refresh, and packaged PTY regressions** — completed.
6. **Append-only independent review** — **changes requested 2026-08-11** in
   `review-2026-08-11T16-48-36Z.md`: correct the filtered/full Sent cursor
   index mismatch and add narrowing, refresh, and cancel regressions.
7. **Re-review** — **changes requested 2026-08-11** in
   `review-2026-08-11T17-24-04Z.md`: source correction accepted; make the
   incremental synthetic fixture's author not match `m`, assert the first row
   was actually filtered out, and prove the restored capture defect fails it.
   **Done and signed off 2026-08-11** in
   `review-2026-08-11T17-33-45Z.md`; the corrected fixture catches the restored
   defect and the focused/PTY suite passes.
8. **Human trial** — pending candidate deployment. Source is signed off;
   Slawomir exercises search during the deployed 1.1 candidate soak before
   final release clearance.
9. **Carry search into Archive** — **deferred to protocol 11 by Slawomir
   2026-08-12**. The earlier 1.1 integration requirement is superseded with
   the participant-local JSON design. Revalidate the same metadata-only
   search/no-claim/no-receipt boundary when protocol 11 adds participant-
   scoped archive metadata to SQLite.
