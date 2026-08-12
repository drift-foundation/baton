# Plan — editor exit enters send confirmation

1. Revalidate `K.EDIT_BODY`, `edit_body_externally`, `arm_send`, and
   `confirm_send` against the current next-generation tree.
2. Add/adjust driver regressions for successful full reply, follow-up, compose,
   and notice editor returns entering `MODE_CONFIRM_SEND` immediately with no
   authority write.
3. Pin decline restoration plus cancellation, editor error, empty-body, and
   attachment-preflight refusal as negative cases.
4. Implement the smallest shared transition by calling the existing
   `arm_send()` only after a successful import; do not duplicate confirmation
   or preflight logic.
5. Run focused state/driver/editor tests, full TUI/core verification, and a
   candidate zipapp PTY trial showing editor exit directly at
   `Send now? [Y/n]`.
6. `baton.implementer` creates and exclusively owns `PROGRESS.md` when this
   child is selected as the current serial item.
7. **Changes requested 2026-08-11**: correct exact whitespace emptiness,
   immediate empty-body refusal/draft preservation, later subject-only fallback,
   and the superseded `edit_body_externally` docstring; add the regressions
   required by `review-2026-08-11T17-19-48Z.md` and return for append-only
   re-review.
8. **Re-review changes requested 2026-08-11**: retain full-body intent in an
   existing quick reply, distinguish explicit-empty refusal from fresh-action
   cancellation, restore the removed draft-preservation assertion, cover fresh
   follow-up and every other ruled mode, and compare published content bytes
   through the public API as required by
   `review-2026-08-11T17-31-16Z.md`.
9. **Re-review 3 changes requested 2026-08-11**: protect compose-mode fresh
   follow-ups after explicit empty, persist that distinct intent through local
   draft retention/reopen without breaking lawful quick follow-up, cover
   handled-message and notice sources plus restart behavior, and restore the
   original assertion as required by
   `review-2026-08-11T17-46-30Z.md`.
10. **Re-review 4 changes requested 2026-08-11**: bump the safety-critical
    local draft format to v3 with explicit v1/v2 migration and required marker,
    persist reply intent too, replace the non-biting restart fixture with a
    genuinely empty follow-up plus later-send refusal, and prevent attachments
    from bypassing explicit-empty intent while retaining lawful attachment-only
    compose. See `review-2026-08-11T17-57-46Z.md`.
11. **Re-review 5 changes requested 2026-08-11**: add the complete v1/v2/v3
    body-intent migration and validation matrix, prove a version-2 reader
    refuses version-3 output, drive the attachment refusal through a genuinely
    empty quoted follow-up without direct state mutation, and correct the stale
    version-2/optional-marker source comments. See
    `review-2026-08-11T18-16-29Z.md`.
12. **Source review signed off 2026-08-11**: the migration matrix, actual
    version-2-reader refusal, reachable quoted-follow-up attachment negative,
    ordinary attachment-only positive, and current-format comments are green.
    See `review-2026-08-11T18-25-02Z.md`. Final candidate build and human soak
    remain owned by the next-release umbrella.
