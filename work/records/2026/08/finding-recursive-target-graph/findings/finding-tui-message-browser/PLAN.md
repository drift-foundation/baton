# Plan

**Status — 2026-08-16:** signed off in
`review-2026-08-16T05-35-02Z.md`; W71 may close satisfying. The detail/tree
ruling in `FINDING.md` supersedes the earlier split-screen proposals.

1. Replace the root-only main table with a bounded two-level containment tree:
   roots plus immediate children, indented `↳`, with visible deeper-child
   disclosure/count. Keep dependency edges out of indentation. Remove `Prog`
   and `Dep` from the table.
2. Make `Enter` always open Work details. Add visible `u` unfold/re-root plus
   breadcrumb and Back/Esc behavior for deeper containment.
3. In Work details, render a bounded selectable Thread list above the selected
   Thread's formatted Messages. Preserve subjects, distinct Threads,
   unseen-first selection and explicit seen-only mutation.
4. Implement/advertise `Ctrl-W` pane navigation (`h/j/k/l`, arrows, `w`, and
   repeated `Ctrl-W`) without consuming more unrelated single-letter keys.
5. Separate references under a `Refs` heading, one canonical reference per
   line. Remove `after #N`; expose continuation and its controls in
   operator-facing terms.
6. Cover roots/children/grandchildren, unfold/back, parent and leaf details,
   multiple Threads, multiple unseen Messages, long bodies/references,
   continuation, seen bounds, wide/narrow fallback, resize and JSON/TUI parity
   wherever projection changes.
7. Replace JSON `dep` with `open_blockers`/`open_dependents`, preserve
   `progress.children/closed`, and show graph counts in Work details/links.
8. Preserve SQLite schema 14, run focused coverage and `just test-v11`, then
   return for review. W92 wakes only after W71 closes satisfying.
