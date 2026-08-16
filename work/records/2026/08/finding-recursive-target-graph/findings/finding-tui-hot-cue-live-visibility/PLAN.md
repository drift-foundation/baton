# Plan

**Status — 2026-08-16:** closed without implementation. The live terminal
began rendering the slow blink after the initial observation; no v11 Work was
created and W84 remains authoritative.

1. Reproduce on the live terminal and record terminal/curses capabilities and
   whether the emitted blink attribute is ignored or visually disabled.
2. Compare minimal phase-cell-only treatments that remain visible without
   sacrificing the authoritative `actve`/`rview` text.
3. Return the presentation choice for review; pin the ruling before coding.
4. Implement focused pure-render, PTY, and live acceptance coverage.
5. Run `just test-v11` and return for independent review.

The investigation steps above are retained as the superseded proposed plan;
they are not actionable after the confirmed live blink.

## Current plan — 2026-08-16

**Status:** queued as a same-schema presentation correction. The closed
no-change disposition is superseded by the bold-Title ruling in `FINDING.md`.

1. Reuse the canonical hot predicate; do not create a second approximation.
2. Compose `A_BOLD` onto the Title cell of every hot row while retaining the
   phase-cell blink and all selection/focus attributes.
3. Prove hot active and review titles are bold, all cold titles are not, blink
   remains phase-cell-only, and narrow layouts remain readable.
4. Exercise PTY output for terminals that expose attributes and pure renderer
   facts for the predicate; run `just test-v11` before review.

**Sequencing clarification — 2026-08-16:** step 3's retained-blink acceptance
applies only to W23's intermediate state. W33 depends on W23 and atomically
removes all Work-row blink styling when it adds claim `Age`. The final
acceptance is bold hot Title plus timer, with no `A_BLINK` emission.

**Narrow supersession — 2026-08-16:** W33 removes indefinite hot-state blink,
not every possible `A_BLINK` emission. It retains the approved client-local
three-scheduled-tick Phase-change blink. W23's implementation and acceptance
remain unchanged: add reliable bold Title while retaining the current
intermediate phase blink until W33 lands.

**Signed off — 2026-08-16:** W23 is accepted in
`review-2026-08-16T15-27-08Z.md`. Focused hot-predicate, cell-attribute,
selection, PTY, narrow, presentation-purity, and dependency-layout coverage
passes independently. W23 may close satisfying and unblock W33.

## Current superseding plan — 2026-08-16

**Status:** approved, queued as new Work; completed W23 is not reopened.

1. Replace the global hot predicate used for Title bold with the
   viewer-relative actionability predicate pinned in `FINDING.md`.
2. Preserve Phase, Current, Age and the short Phase-change blink as the shared
   activity evidence; do not hide another participant's execution facts.
3. Cover a ready unclaimed single-handler assignment, competing eligible
   handlers before claim, the winning claimant after claim, another viewer's
   active Work, blocked/waiting/parked/closed Current assignments, and a
   personal `@` obligation.
4. Prove JSON/TUI parity for the underlying viewer-relative facts and ensure
   bold remains Title-cell-only at wide and narrow widths.

**Review status — 2026-08-16 16:25Z:** changes requested in
`review-2026-08-16T16-25-18Z.md`. The focused predicate/render suite is clean,
but the required multi-handler boundary is not covered: current tests compare
one eligible handler with an intentionally ineligible teammate. Add a real
two-eligible-handler before-claim/bold-for-both and after-claim/bold-only-for-
winner regression, preserving the ineligible negative case, then return W81
for re-review.

**Signed off — 2026-08-16 16:30Z:** the second review in
`review-2026-08-16T16-30-35Z.md` accepts the added two-eligible-handler
regression. Focused coverage and the complete v11 parallel plus serial gate are
green. W81 may close satisfying.
