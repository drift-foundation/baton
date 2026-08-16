# Plan

Queued as non-blocking feedback from the first human v11 trial.

1. Implement the confirmed stacked split: Work table above and the highlighted
   Work's selected Thread messages below.
2. Keep `Enter` in the Work pane as child drill-down; use `Tab` for pane focus
   and provide visible hints for switching distinct Threads and explicitly
   marking the displayed page seen.
3. A nonzero `New` counter selects an unseen Thread in the `Msgs` pane and
   therefore has an immediate visible route to its contributing messages.
4. Add real-PTY coverage for parent Work, leaf Work, no-discussion leaf Work,
   return navigation, and preservation of explicit seen semantics.
5. Include the accepted correction in a later immutable v11 distribution.
