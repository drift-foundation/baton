# Plan

1. Revalidate W39358's operator and W39364's retained attempt evidence against
   the current tree.
2. Pin the exact explicit disposition operand and retained-ending semantics.
3. Implement the smallest operator-only correction and focused injected tests.
4. Prove a retained candidate remains publicly readable after terminal
   cleanup, including one real-Docker gate with no live provider.
5. Return for independent review before authorizing another useful-task run.
6. Make the terminal locator proof establish that the retained proposal can
   actually be opened, not only that `stat` classifies its path as a
   directory; add the negative unreadable-directory regression.
7. Re-run the focused and real-Docker gates and return for independent review.
8. Complete the terminal proof for the operations it claims to support:
   require the proposal's `candidate` directory and prove regular candidate
   files can be opened rather than merely `stat`ed.
9. Add missing-candidate and unreadable-file regressions, rerun the shared
   operator suite after W51476's concurrent edit settles, and return for
   independent review.

Outcome: all nine steps are complete and independently accepted in
`review-2026-08-31T05-44-46Z.md`. This closes the retention correction; it
does not itself authorize W51487's separate live provider attempt.
