# Plan

**Status — 2026-08-16 11:31Z:** active with `baton.implementer` in the
pre-cutover cleanup batch; live W9 was passed to `baton.impl` at authority
sequence 150 and returns next to `baton.bug`. It is a same-schema TUI
correction and must not be copied into the fresh authority as unfinished Work.

1. Add the confirmed `Exit? y/N` state to normal TUI navigation.
2. Preserve text-entry handling and return to the exact prior view on cancel.
3. Add real-PTY coverage for confirm, cancel by each accepted key, irrelevant
   keys, one-row narrow rendering, and absence of authority/seen mutation.
4. Include the accepted correction in the next immutable v11 distribution.
5. Remove this Work from the fresh-authority recreation inventory and update
   its counts/proof after focused and full v11 verification pass.

**Closed satisfying — 2026-08-16 11:42Z.** Final review is clean at
`review-2026-08-16T11-42-38Z.md`; the live Work closed at authority sequence
154. The implementation reports 640 parallel plus 3 serial tests green, and
the four focused confirmation/PTY targets and final diff check pass. W9 is
removed from W92's recreation set. Deployment remains held by the continuing
pre-cutover audit and its other same-schema corrections.
