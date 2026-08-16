# Plan

**Status — 2026-08-16 11:22Z:** active with `baton.implementer` in the
pre-cutover cleanup batch; live W6 was passed to `baton.impl` at authority
sequence 143 and returns next to `baton.bug`. It is a same-schema presentation
correction and must not be copied into the fresh authority as unfinished Work.

1. Change only the compact TUI mapping for `confirmed-defect` from `cnfrm` to
   `defct`.
2. Pin the mapping in focused renderer and real-PTY coverage while retaining
   the canonical JSON value.
3. Include the correction in the next immutable v11 distribution.
4. Remove W6 from the fresh-authority recreation inventory and update its
   expected counts/proof after focused and full v11 verification pass.

**Closed satisfying — 2026-08-16 11:31Z.** Final review is clean at
`review-2026-08-16T11-31-10Z.md`; the live Work closed at authority sequence
148. The implementation reports 637 parallel plus 3 serial tests green, and
the focused mapping/projection/PTY targets and final diff check pass. W6 is
removed from W92's recreation set. Deployment remains held by the continuing
pre-cutover audit and its other same-schema corrections.
