# Plan

1. Revalidate batch behavior against the accepted key/value command
   specification, command-bar identity guard, WS-5 retry model, TUI layout,
   terminal paste behavior, and authority refusal semantics.
2. Define explicit batch-buffer state, cursor/editing behavior, `::` entry,
   Enter-as-newline, visible `Ctrl-G` Go, cancellation, and non-empty-buffer
   protection without changing the one-line `:` interaction.
3. Preflight every line through the shared parser before execution. Then run
   sequentially, stop on the first authority refusal, and preserve honest
   completed/failed/unrun results with safe per-line operation identity.
4. Add pure-state and virtual/real-terminal regressions for typed and pasted
   batches, syntax failure before execution, mid-batch authority refusal,
   interruption/retry, duplicate commands, quoting, resize/narrow screens,
   cancellation, and proof that staging alone causes no authority mutation.
5. Verify dependency on the key/value grammar, focused coverage, and
   `just test-v11`, then return for review before the next immutable release.
