# Plan

1. [done 2026-08-27] Confirm focusable breadcrumbs, `h`/`l` and cursor parity,
   Enter navigation, region cycling, horizontal visibility, textual selection
   feedback, and history-versus-hierarchy semantics.
2. [done 2026-08-27] Revalidated every breadcrumb page, focus graph,
   viewport/key owner, one-step Back contract, narrow behavior, and the W26328
   interaction. Recorded exact decision support and a 10-case green baseline
   in `evidence/reviewer-research-2026-08-27.md`.
3. [done approver 2026-08-27] Confirmed the structured location-reset model,
   Tab/Shift-Tab and Work-detail Ctrl-W graph, boundary Up/Down, same-tab Work
   jumps, exact page restoration, focused Left-versus-Esc rule, compact
   selectors, whole-token `…` viewport, and footer/narrow refusal.
4. [done tuner 2026-08-28 UTC] Added the separate structural-location model,
   shared structured crumb targets, complete focus graph, one-action direct
   navigation, whole-token viewport/footer, operator guide, and focused
   deep/history/purity/narrow-terminal regressions. Full v11 verification:
   3239 parallel, 54 serial/PTY and 77 ACP passed.
5. [done tuner; awaiting re-review 2026-08-28 UTC] Corrected the independent
   review's non-unique repeated-Work crumb keys, focused Up/k body fallthrough,
   and code-point viewport fitting. Added the requested graph-recenter,
   all-single-body/dual-Up, wide-character and combining-character regressions.
   Verification: 48 focused, 294 affected, 3252 full parallel, 54 serial/PTY
   and 77 ACP passed. Re-review against
   `review-2026-08-28T04-32-38Z.md`.
6. [signed off reviewer 2026-08-28 UTC] Independently accepted all three
   corrections: 48 focused and 294 affected tests pass. Application work is
   complete. Terminal dossier closure awaits approver resolution of the
   still-missing implementer-owned `PROGRESS.md`; see
   `review-2026-08-28T04-46-59Z.md`.
7. [done approver 2026-08-28 UTC] Superseded the Claude-only progress rule.
   The participant that actually performs an implementation change owns its
   attributable `PROGRESS.md` entry; review-only participants still do not.
8. [done tuner 2026-08-28 UTC] Added the truthful tuner-authored `PROGRESS.md`
   for the original implementation and review correction under the approver's
   change-author ownership ruling.
9. [next approver] Satisfying closure. Application review is signed off and no
   further application review cycle is required.
