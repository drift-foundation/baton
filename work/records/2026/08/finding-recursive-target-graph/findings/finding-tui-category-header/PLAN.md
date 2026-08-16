# Plan

**Status — 2026-08-16:** implemented and review-clean; ready for the next
checkpoint/distribution.

1. [done] Change only the displayed Work-table classification header from `Cls` to
   `Cat`; retain canonical `classification` everywhere outside presentation.
2. [done] Update wide, narrow, and responsive-column coverage so `Cat` appears when
   the category column is present and disappears as a whole when omitted.
3. [done] Verify JSON/TUI parity, packaged TUI behavior, and the full v11 gate before
   review.
