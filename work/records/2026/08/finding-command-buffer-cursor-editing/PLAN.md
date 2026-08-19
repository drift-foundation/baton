# Plan

1. [done] Reproduced the reported limitation from the current command input
   code and identified the suffix-only W26 regression gap.
2. [done] Approved the non-modal editing contract in `FINDING.md`: cursor and
   boundary keys edit at an explicit caret, printable keys remain literal,
   and Esc still cancels.
3. [done] Add explicit command-caret state, cursor-relative
   insertion/deletion, and caret-aware horizontal viewporting without changing
   the canonical command grammar or authority boundary.
4. [done] Add focused pure-state and real-terminal coverage
   for interior editing, history immutability, Unicode/display cells, resize,
   completion, reverse search, contextual seeding, cancel, and submission.
5. [done] Independently verify the frozen implementation and full
   v11 gate before closure.
