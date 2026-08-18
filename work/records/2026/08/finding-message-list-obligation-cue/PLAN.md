# Plan

**Status — signed off 2026-08-18 by `baton.codex`.** The R1 defect (a fixed-width `Do` cell truncating
`@1000` into the different valid-looking selector `@100`) is fixed: the cue
column is now sized from the page like `Id`, with the declared width as a
minimum rather than a cap. See `review-2026-08-18T19-50-38Z.md` for the
finding and the `R1` section of `PROGRESS.md` for the response, the break-sweep
and one repair to the reviewer's own test. Independent confirmation is in
`review-2026-08-18T20-56-21Z.md`.


1. [done] Record the observed missing per-Message action cue and the approved
   viewer-relative behavior.
2. [done] Revalidate the Message-list projection and fixed-column work so
   the cue consumes canonical obligation data without duplicating authority.
3. [done] Implement the compact row cue and selected-row action guidance,
   including deterministic narrow-width behavior.
4. [done] Add focused positive, negative, lifecycle, refresh, width, and
   navigation regressions.
5. [done] Independently review the live TUI and JSON/TUI parity.
