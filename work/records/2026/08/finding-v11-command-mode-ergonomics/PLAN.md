# Plan

**Status — complete and independently signed off 2026-08-18.** W26 searchable
history and W27 grammar-derived completion are both closed satisfying. Their
combined history/search/completion interaction passes 93 focused tests,
including real-terminal coverage, without an authority schema change. See
`review-2026-08-18T20-55-00Z.md`.

1. [done] Implement and review searchable command history from
   `findings/finding-searchable-command-history/`.
2. [done] Implement and review grammar-derived completion from
   `findings/finding-command-completion/`.
3. [done] Exercise the combined interaction on a real PTY: history selection followed
   by a small edit and completion, quoted values, narrow terminals, resize,
   cancellation, and proof that no authority bytes or refresh state change
   before submission.
4. [done] Run the focused v11 TUI/grammar tests and `just test-v11`, then return the
   track for independent review.
